import re

ALLOWED_START = ("select",)

DISALLOWED = [
    "delete", "update", "insert",
    "drop", "truncate", "alter", "create"
]

def validate_sql(sql: str):
    s = sql.strip().lower()

    if not s:
        raise Exception("Empty SQL")

    if not s.startswith(ALLOWED_START):
        raise Exception("Only SELECT statements allowed")

    for kw in DISALLOWED:
        if re.search(rf"\b{kw}\b", s):
            raise Exception("Destructive SQL not allowed")

    if ";" in s[:-1]:
        raise Exception("Multiple statements detected")

    return True


def _sanitize_identifier(name: str) -> str:
    name = name.strip()
    # strip common quoting styles: `name`, "name", [name]
    if (name.startswith("`") and name.endswith("`")) or (name.startswith('"') and name.endswith('"')):
        name = name[1:-1]
    if name.startswith("[") and name.endswith("]"):
        name = name[1:-1]
    # if schema-qualified, use the last part
    if "." in name:
        name = name.split(".")[-1]
    return name


def parse_schema(schema: str) -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    text = schema or ""
    # support multiple CREATE TABLE statements
    for m in re.finditer(r"create\s+table\s+([^\s(]+)\s*\((.*?)\)", text, flags=re.IGNORECASE | re.DOTALL):
        raw_table = m.group(1)
        cols_block = m.group(2)
        table = _sanitize_identifier(raw_table)
        cols: set[str] = set()
        # split by commas at top level; simple heuristic
        for line in cols_block.split(","):
            token = line.strip()
            if not token:
                continue
            # skip table-level constraints
            if re.match(r"^(primary|foreign|unique|constraint)\b", token, flags=re.IGNORECASE):
                continue
            # first word is the column name
            col = token.split()[0]
            col = _sanitize_identifier(col)
            if col:
                cols.add(col.lower())
        if table:
            tables[table.lower()] = cols
    return tables


def validate_schema_references(schema: str, sql: str) -> None:
    tables = parse_schema(schema)
    if not tables:
        return
    s = sql or ""
    low = s.lower()
    errors: list[str] = []

    ast_tables: set[str] = set()
    ast_qualified: list[tuple[str, str]] = []
    ast_bare_cols: set[str] = set()
    try:
        import sqlglot
        from sqlglot import exp
        tree = sqlglot.parse_one(s)
        for t in tree.find_all(exp.Table):
            ast_tables.add(_sanitize_identifier(t.name).lower())
        for c in tree.find_all(exp.Column):
            if c.table:
                ast_qualified.append((_sanitize_identifier(str(c.table)), _sanitize_identifier(c.name)))
            else:
                ast_bare_cols.add(_sanitize_identifier(c.name).lower())
    except Exception:
        pass

    # find tables used in FROM/JOIN
    from_join = re.findall(r"(?:from|join)\s+([^\s,;]+)", low, flags=re.IGNORECASE)
    used_tables: set[str] = set(_sanitize_identifier(t).lower() for t in from_join)
    if ast_tables:
        used_tables |= ast_tables
    # verify tables exist
    unknown_tables = [t for t in used_tables if t not in tables]
    if unknown_tables:
        errors.append(f"Unknown table(s) referenced: {', '.join(sorted(set(unknown_tables)))}")

    # verify qualified column references table.column
    qualified = [(tbl, col) for tbl, col in re.findall(r"([a-zA-Z_][\w]*)\s*\.\s*([a-zA-Z_][\w]*)", low)]
    qualified += ast_qualified
    for tbl, col in qualified:
        t = _sanitize_identifier(tbl).lower()
        c = _sanitize_identifier(col).lower()
        if t not in tables:
            errors.append(f"Unknown table in column reference: {tbl}.{col}")
            continue
        if c not in tables[t]:
            errors.append(f"Unknown column '{col}' in table '{tbl}'")

    # if multiple tables used, flag ambiguous bare columns if they exist in >1 tables
    if len(used_tables) > 1:
        all_cols: dict[str, int] = {}
        for cols in tables.values():
            for c in cols:
                all_cols[c] = all_cols.get(c, 0) + 1
        ambiguous = {c for c, cnt in all_cols.items() if cnt > 1}
        for c in ambiguous:
            # bare occurrence (not part of table.column), approximate check
            if re.search(rf"\b{re.escape(c)}\b(?!\s*\.)", low):
                errors.append(f"Ambiguous unqualified column '{c}' in multi-table query")
    else:
        # single-table query: detect unknown bare columns
        # select the single table
        single_table = next(iter(used_tables)) if used_tables else None
        if single_table and single_table in tables:
            known_cols = tables[single_table]
            # detect alias in FROM clause to exclude it
            alias = None
            m_from = re.search(rf"from\s+([^\s,;]+)\s+([a-zA-Z_][\w]*)", low, flags=re.IGNORECASE)
            if m_from:
                alias = _sanitize_identifier(m_from.group(2)).lower()
            # collect all bare word tokens
            tokens = set(re.findall(r"\b([a-zA-Z_][\w]*)\b", low))
            tokens |= ast_bare_cols
            # remove keywords and common functions
            KEYWORDS = {
                "select","from","where","group","by","order","as","on","and","or","not","null",
                "sum","count","avg","min","max","coalesce","case","when","then","else","end",
                "distinct","having","join","left","inner","right","union","all","limit","offset",
                "fetch","first","row","rows","top","like","in","exists","is","between"
            }
            candidates = {t for t in tokens if t not in KEYWORDS}
            # exclude table names, alias, and columns already seen as qualified
            qualified_cols = {c for _, c in re.findall(r"([a-zA-Z_][\w]*)\s*\.\s*([a-zA-Z_][\w]*)", low)}
            qualified_cols |= {c for _, c in ast_qualified}
            exclude = set(used_tables)
            if alias:
                exclude.add(alias)
            candidates = {t for t in candidates if t not in exclude and t not in qualified_cols}
            unknown_bare = {t for t in candidates if t not in known_cols}
            if unknown_bare:
                errors.append("Unknown column(s) in single-table query: " + ", ".join(sorted(unknown_bare)))

    if errors:
        raise ValueError("\n".join(errors))

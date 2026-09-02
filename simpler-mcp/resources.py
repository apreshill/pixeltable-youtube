"""Read-only descriptions of the ``mcp_demo`` Pixeltable catalog."""

from typing import Any

import pixeltable as pxt

CATALOG = 'mcp_demo'


def list_catalog() -> dict[str, list[str]]:
    """List the tables and views available through this MCP."""

    contents = pxt.get_dir_contents(CATALOG)
    return {
        'tables': [path.rsplit('/', 1)[-1] for path in contents['tables']],
        'dirs': [path.rsplit('/', 1)[-1] for path in contents['dirs']],
    }


def describe_table(name: str) -> dict[str, Any]:
    """Describe one table or view inside ``mcp_demo``."""

    if '/' in name or '.' in name:
        raise ValueError('Pass a table name inside mcp_demo, not a catalog path.')
    table = pxt.get_table(f'{CATALOG}.{name}')
    version = table._tbl_version.get()
    return {
        'name': name,
        'columns': {column: str(column_type) for column, column_type in table._get_schema().items()},
        'computed_columns': {
            column.name: str(column.value_expr)
            for column in version.cols_by_name.values()
            if column.is_computed and column.name is not None
        },
        'indexes': [
            {
                'name': index_name,
                'column': index_info.col.name,
                'type': type(index_info.idx).__name__,
            }
            for index_name, index_info in version.idxs_by_name.items()
        ],
        'row_count': table.count(),
    }

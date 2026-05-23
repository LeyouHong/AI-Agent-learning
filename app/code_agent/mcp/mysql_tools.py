from typing import Optional, Dict, Any, Annotated, List

import pymysql
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP()


class Response(BaseModel):
    success: bool
    database: str
    table: str
    data: Optional[dict] | Optional[list]
    rowcount: Optional[int] = None


MYSQL_CONFIG = {
    "host": "192.168.64.2",
    "port": 3306,
    "user": "root",
    "password": "root",
    "charset": "utf8mb4",
}


def get_connection(db):
    config = MYSQL_CONFIG.copy()
    if db:
        config["database"] = db

    try:
        connection = pymysql.connect(**config)
        return connection
    except Exception as e:
        msg = f"MySQL connection error: {str(e)}"
        return msg


def execute_query(command, database=None, params=None, commit=False):
    try:
        connection = get_connection(database)

        if not isinstance(connection, pymysql.Connection):
            return connection

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(command, params)
            result = cursor.fetchall()

            if commit:
                connection.commit()

            return result, cursor.rowcount

    except Exception as e:
        raise e


# =========================
# Tools
# =========================

@mcp.tool(name="mysql_list_databases", description="List all MySQL databases")
def mysql_list_databases():
    try:
        result, rowcount = execute_query("SHOW DATABASES")
        databases = [row["Database"] for row in result]

        return Response(
            success=True,
            database="",
            table="",
            data=databases,
            rowcount=rowcount,
        )
    except Exception as e:
        return f"List databases error: {str(e)}"


@mcp.tool(name="mysql_list_tables", description="List tables in a database")
def mysql_list_tables(database: str):
    try:
        result, rowcount = execute_query("SHOW TABLES", database=database)
        tables = [list(row.values())[0] for row in result]

        return Response(
            success=True,
            database=database,
            table="",
            data=tables,
            rowcount=rowcount,
        )
    except Exception as e:
        return f"List tables error: {str(e)}"


@mcp.tool(name="mysql_describe_tables", description="Describe table schema")
def mysql_describe_tables(database: str, table: str):
    try:
        result, rowcount = execute_query(f"DESCRIBE {table}", database=database)

        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        return f"Describe tables error: {str(e)}"


@mcp.tool(name="mysql_execute_query", description="Execute SQL query")
def mysql_execute_query(command, database=None, params: Optional[list] = None):
    try:
        params_tuple = tuple(params) if params else None
        result, rowcount = execute_query(command, database=database, params=params_tuple)

        return Response(
            success=True,
            database=database or "",
            table="",
            data=result,
            rowcount=rowcount,
        )
    except Exception as e:
        return f"Query error: {str(e)}"


@mcp.tool(name="mysql_insert_data", description="Insert data into table")
def mysql_insert_data(database: str, table: str, data: Dict[str, str]):
    columns = list(data.keys())
    values = list(data.values())
    placeholders = ", ".join(["%s"] * len(values))

    command = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

    try:
        result, rowcount = execute_query(
            command,
            database=database,
            params=tuple(values),
            commit=True,
        )

        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )

    except Exception as e:
        return f"Insert error: {str(e)}"


@mcp.tool(name="mysql_update_data", description="Update table data")
def mysql_update_data(database: str, table: str, data: Dict[str, str], where: Dict[str, str]):
    set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
    where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])

    command = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

    params = list(data.values()) + list(where.values())

    try:
        result, rowcount = execute_query(
            command,
            database=database,
            params=tuple(params),
            commit=True,
        )

        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )

    except Exception as e:
        return f"Update error: {str(e)}"


@mcp.tool(name="mysql_delete_data", description="Delete table data")
def mysql_delete_data(database: str, table: str, where: Dict[str, str]):
    where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
    command = f"DELETE FROM {table} WHERE {where_clause}"

    try:
        result, rowcount = execute_query(
            command,
            database=database,
            params=tuple(where.values()),
            commit=True,
        )

        return Response(
            success=True,
            database=database,
            table=table,
            data=result,
            rowcount=rowcount,
        )

    except Exception as e:
        return f"Delete error: {str(e)}"


@mcp.tool(name="mysql_create_database", description="Create database")
def mysql_create_database(database_name: str, charset: str = "utf8mb4"):
    command = f"CREATE DATABASE {database_name} CHARACTER SET {charset}"

    try:
        result, rowcount = execute_query(command)

        return Response(
            success=True,
            database=database_name,
            table="",
            data=result,
            rowcount=rowcount,
        )

    except Exception as e:
        return f"Create database error: {str(e)}"


@mcp.tool(name="mysql_create_table", description="Create table")
def mysql_create_table(
    database: str,
    table_name: str,
    table_columns: Annotated[
        str,
        Field(
            description="SQL column definitions for CREATE TABLE",
            json_schema_extra={
                "example": "`id` int NOT NULL AUTO_INCREMENT, `name` varchar(255) NOT NULL, PRIMARY KEY (`id`)"
            },
        ),
    ],
    table_schema: Annotated[
        str,
        Field(
            description="Additional table options",
            json_schema_extra={
                "example": "ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
            },
        ),
    ],
):
    command = f"CREATE TABLE {table_name} ({table_columns}) {table_schema}"

    try:
        result, rowcount = execute_query(command, database=database)

        return Response(
            success=True,
            database=database,
            table=table_name,
            data=result,
            rowcount=rowcount,
        )

    except Exception as e:
        return f"Create table error: {str(e)}"


@mcp.tool(name="mysql_execute_command", description="Execute SQL command (DDL)")
def mysql_execute_command(database: str, command: str):
    try:
        result, rowcount = execute_query(
            command,
            database=database,
            commit=True,
        )

        return Response(
            success=True,
            database=database,
            table="",
            data=result,
            rowcount=rowcount,
        )

    except Exception as e:
        return f"Execute command error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")

    # Debug examples
    # print(mysql_list_databases())
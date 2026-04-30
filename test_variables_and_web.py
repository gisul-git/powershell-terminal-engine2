import asyncio

from execution_engine import execute_command
from session_manager import create_session


async def test_variables_and_web_commands():
    session = create_session()

    await execute_command(session, "$name = John")
    result = await execute_command(session, "echo $name")
    assert result["output"] == "John"

    await execute_command(session, "Set-Variable city Bangalore")
    result = await execute_command(session, "Get-Variable city")
    assert "Name : city" in result["output"]
    assert "Value : Bangalore" in result["output"]

    await execute_command(session, "Remove-Variable city")
    result = await execute_command(session, "Get-Variable city")
    assert result["output"] == "variable not found"

    result = await execute_command(session, "Invoke-WebRequest https://example.com")
    assert "StatusCode : 200" in result["output"]

    result = await execute_command(session, "Invoke-RestMethod https://jsonplaceholder.typicode.com/todos/1")
    assert "title :" in result["output"]
    assert "completed :" in result["output"]

    result = await execute_command(
        session,
        "Invoke-RestMethod https://jsonplaceholder.typicode.com/todos/1 | Select-Object title",
    )
    assert result["output"]
    assert "title :" not in result["output"]

    result = await execute_command(session, "Get-Variable | Sort-Object")
    assert "name" in result["output"]

    result = await execute_command(session, "Invoke-WebRequest http://127.0.0.1")
    assert result["output"] == "Access denied"


if __name__ == "__main__":
    asyncio.run(test_variables_and_web_commands())
    print("Variable and web command tests passed")

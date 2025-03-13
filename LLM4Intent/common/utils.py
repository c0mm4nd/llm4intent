import logging
from typing import Any, Dict, List, Literal, Tuple, Union, get_type_hints

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger


def get_prompt(agent_name: str) -> str:
    with open(f"LLM4Intent/prompts/{agent_name}_prompt.txt") as f:
        return f.read()


# Python 类型到 JSON Schema 类型的映射
PYTHON_TO_JSON = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    type(None): "null",
}


def convert_type_to_json_schema(py_type: Any) -> dict:
    """将 Python 类型转换为 JSON Schema 类型"""

    # 处理基本类型
    if py_type in PYTHON_TO_JSON:
        return {"type": PYTHON_TO_JSON[py_type]}

    # 处理可选类型 Optional[T] (实际上是 Union[T, None])
    if hasattr(py_type, "__origin__") and py_type.__origin__ is Union:
        subtypes = [convert_type_to_json_schema(t) for t in py_type.__args__]
        if any(t.get("type") == "null" for t in subtypes):
            return {"oneOf": [t for t in subtypes if t.get("type") != "null"]}

    # 处理列表 List[T] -> {"type": "array", "items": {T}}
    if hasattr(py_type, "__origin__") and py_type.__origin__ in (list, List):
        item_type = convert_type_to_json_schema(py_type.__args__[0])
        return {"type": "array", "items": item_type}

    # 处理元组 Tuple[T1, T2, ...] -> {"type": "array", "items": [{T1}, {T2}, ...]}
    if hasattr(py_type, "__origin__") and py_type.__origin__ in (tuple, Tuple):
        item_types = [convert_type_to_json_schema(t) for t in py_type.__args__]
        return {"type": "array", "items": item_types}

    # 处理字典 Dict[K, V] -> {"type": "object"}
    if hasattr(py_type, "__origin__") and py_type.__origin__ in (dict, Dict):
        return {"type": "object"}

    # 处理 Literal["a", "b"] -> {"enum": ["a", "b"]}
    if hasattr(py_type, "__origin__") and py_type.__origin__ is Literal:
        return {"enum": list(py_type.__args__)}

    return {"type": "object"}  # 默认返回 object


def convert_tool(tool):

    hints = get_type_hints(tool)
    parameters = {
        k: convert_type_to_json_schema(v)
        for k, v in hints.items()
        if k != "return" and k != "self"
    }
    required = list(parameters.keys())
    return_type = hints.get("return", None)
    return_schema = convert_type_to_json_schema(return_type)

    return {
        "type": "function",
        "function": {
            "name": tool.__name__,
            "description": tool.__doc__ or f"Tool: {tool.__name__}",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
            "returns": return_schema,
        },
    }

from LLM4Intent.roles.checker import CheckReport

def test_CheckReport_pydantic_to_openai():
    # try convert to openai format
    report_json = CheckReport.model_json_schema()
    print(report_json)

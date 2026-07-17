from fastapi.responses import Response

from cat import endpoint


ANSWER_XML = (
    "<Response><Speak>Hello from the Cheshire Cat, powered by Plivo.</Speak></Response>"
)


@endpoint.post("/plivo/answer", tags=["Plivo"])
async def plivo_answer() -> Response:
    return Response(content=ANSWER_XML, media_type="application/xml")

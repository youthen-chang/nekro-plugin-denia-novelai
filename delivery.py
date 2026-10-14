"""Convert plugin-owned images to NekroAgent chat upload paths before sending."""
from pathlib import Path


async def prepare_chat_image(file_path, chat_key):
    # The ordinary slash-command pipeline materializes files automatically.
    # Direct AgentCtx.send_image expects /app/uploads or /app/shared instead.
    from nekro_agent.tools.common_util import copy_to_upload_dir
    from nekro_agent.tools.path_convertor import (
        convert_filename_to_sandbox_upload_path,
        convert_to_host_path,
    )

    source = Path(file_path).resolve(strict=True)
    if not source.is_file():
        raise ValueError('Generated image is not a file')
    copied_path, copied_name = await copy_to_upload_dir(
        file_path=str(source), file_name=source.name, from_chat_key=chat_key,
    )
    sandbox_path = convert_filename_to_sandbox_upload_path(copied_name)
    # Check the same resolver used by the real send pipeline, including chat-key
    # sanitization. This does not send messages or call the image-generation API.
    resolved = convert_to_host_path(sandbox_path, chat_key)
    if resolved.resolve() != Path(copied_path).resolve() or not resolved.is_file():
        raise ValueError('Prepared image path does not resolve to its upload file')
    return str(sandbox_path)


async def send_command_response(ctx, chat_key, response):
    """Prepare original command media, then send one message without a prefix."""
    from nekro_agent.services.command.output import materialize_command_response
    from nekro_agent.services.command.schemas import CommandOutputSegmentType
    from nekro_agent.adapters.interface.schemas.platform import (
        PlatformSendRequest, PlatformSendSegment, PlatformSendSegmentType,
    )

    prepared = await materialize_command_response(chat_key, response)
    if not prepared.output_segments:
        if prepared.message:
            await ctx.send_text(prepared.message, record=False)
        return
    segments = []
    if prepared.message:
        segments.append(PlatformSendSegment(type=PlatformSendSegmentType.TEXT,content=prepared.message))
    for segment in prepared.output_segments:
        if segment.type == CommandOutputSegmentType.TEXT and segment.text:
            segments.append(PlatformSendSegment(type=PlatformSendSegmentType.TEXT,content=segment.text))
        elif segment.type == CommandOutputSegmentType.IMAGE and segment.file_path:
            segments.append(PlatformSendSegment(type=PlatformSendSegmentType.IMAGE,file_path=segment.file_path))
        elif segment.type == CommandOutputSegmentType.FILE and segment.file_path:
            segments.append(PlatformSendSegment(type=PlatformSendSegmentType.FILE,file_path=segment.file_path))
    if segments:
        result = await ctx.adapter.forward_message(PlatformSendRequest(chat_key=chat_key,segments=segments))
        if not result.success:
            raise ValueError('Combined image response could not be delivered')

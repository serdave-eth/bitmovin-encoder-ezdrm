import time
from os import path

#from bitmovin_api_sdk import AacAudioConfiguration, AclEntry, AclPermission, BitmovinApi, \
#    BitmovinApiLogger, CencDrm, CencWidevine, CencPlayReady, CencFairPlay, CodecConfiguration, DashManifest, \
#    DashManifestDefault, DashManifestDefaultVersion, Encoding, EncodingOutput, Fmp4Muxing, \
#    H264VideoConfiguration, HlsManifest, HlsManifestDefault, HlsManifestDefaultVersion, HttpInput, \
#    Input, ManifestGenerator, ManifestResource, MessageType, Muxing, MuxingStream, Output, \
#    PresetConfiguration, S3Output, StartEncodingRequest, Status, Stream, StreamInput, StreamSelectionMode, Task

from bitmovin_api_sdk import *

# Hardcoded configuration parameters

BITMOVIN_API_KEY = ""
HTTP_INPUT_HOST = ""
HTTP_INPUT_FILE_PATH = "" #when you get the shareable link from dropbox, everything from the backslash onwards should go here. Change dl=0 to dl=1
S3_OUTPUT_BUCKET_NAME = ""
S3_OUTPUT_ACCESS_KEY = "" # When you set up the S3 bucket, make sure that programmatic access is enabled. Once it is you can get the access key and secret key.
S3_OUTPUT_SECRET_KEY = ""
S3_OUTPUT_BASE_PATH = "" # Make sure you have no back slash here
DRM_KEY = ""
DRM_FAIRPLAY_IV = ""
DRM_FAIRPLAY_URI = ""
DRM_WIDEVINE_KID = "" #EZDRM Widevine KID Hex
DRM_WIDEVINE_PSSH = "" #EZDRM Widevine PSSH
DRM_FAIRPLAY_LAURL = ""
EXAMPLE_NAME = "" # This is the name of the folder that will be added to the output S3 bucket
bitmovin_api = BitmovinApi(api_key=BITMOVIN_API_KEY, logger=BitmovinApiLogger())

def main():
    encoding = _create_encoding(name=EXAMPLE_NAME, description="Example with CENC DRM content protection")

    http_input = _create_http_input(host=HTTP_INPUT_HOST)
    input_file_path = HTTP_INPUT_FILE_PATH

    output = _create_s3_output(
        bucket_name=S3_OUTPUT_BUCKET_NAME,
        access_key=S3_OUTPUT_ACCESS_KEY,
        secret_key=S3_OUTPUT_SECRET_KEY
    )
   #output = _get_cdn_output()

    h264_video_configuration = _create_h264_video_configuration()
    
    h264_video_stream = _create_stream(
        encoding=encoding,
        encoding_input=http_input,
        input_path=input_file_path,
        codec_configuration=h264_video_configuration
    )

    aac_audio_configuration = _create_aac_audio_configuration()
    aac_audio_stream = _create_stream(
        encoding=encoding,
        encoding_input=http_input,
        input_path=input_file_path,
        codec_configuration=aac_audio_configuration
    )

    video_muxing = _create_fmp4_muxing(encoding=encoding, stream=h264_video_stream)
    audio_muxing = _create_fmp4_muxing(encoding=encoding, stream=aac_audio_stream)

    _create_drm_config(encoding=encoding, muxing=video_muxing, output=output, output_path="video")
    _create_drm_config(encoding=encoding, muxing=audio_muxing, output=output, output_path="audio")

    #dash_manifest = _create_default_dash_manifest(encoding=encoding, output=output, output_path="")
    hls_manifest = _create_default_hls_manifest(encoding=encoding, output=output, output_path="")

    start_encoding_request = StartEncodingRequest(
        manifest_generator=ManifestGenerator.V2,
        #vod_dash_manifests=[ManifestResource(manifest_id=dash_manifest.id)],
        vod_hls_manifests=[ManifestResource(manifest_id=hls_manifest.id)]
    )

    _execute_encoding(encoding=encoding, start_encoding_request=start_encoding_request)

def _get_cdn_output() -> CdnOutput:
    """
    Retrieves the singleton CdnOutput resource that exists for every organization

    <p>API endpoint:
    https://bitmovin.com/docs/encoding/api-reference/all#/Encoding/GetEncodingOutputsCdn
    """
    cdn_outputs = bitmovin_api.encoding.outputs.cdn.list().items

    return cdn_outputs[0]

def _create_encoding(name, description):
    encoding = Encoding(name=name, description=description)
    return bitmovin_api.encoding.encodings.create(encoding=encoding)

def _create_http_input(host):
    http_input = HttpInput(host=host)
    return bitmovin_api.encoding.inputs.http.create(http_input=http_input)

def _create_s3_output(bucket_name, access_key, secret_key):
    s3_output = S3Output(bucket_name=bucket_name, access_key=access_key, secret_key=secret_key)
    return bitmovin_api.encoding.outputs.s3.create(s3_output=s3_output)

def _create_h264_video_configuration():
    config = H264VideoConfiguration(name="H.264 1080p 1.5 Mbit/s", preset_configuration=PresetConfiguration.VOD_STANDARD, height=1080, bitrate=1500000)
    return bitmovin_api.encoding.configurations.video.h264.create(h264_video_configuration=config)

def _create_aac_audio_configuration():
    config = AacAudioConfiguration(name="AAC 128 kbit/s", bitrate=128000)
    return bitmovin_api.encoding.configurations.audio.aac.create(aac_audio_configuration=config)

def _create_stream(encoding, encoding_input, input_path, codec_configuration):
    stream_input = StreamInput(input_id=encoding_input.id, input_path=input_path, selection_mode=StreamSelectionMode.AUTO)
    stream = Stream(input_streams=[stream_input], codec_config_id=codec_configuration.id)
    return bitmovin_api.encoding.encodings.streams.create(encoding_id=encoding.id, stream=stream)

def _create_fmp4_muxing(encoding, stream):
    muxing = Fmp4Muxing(segment_length=4.0, streams=[MuxingStream(stream_id=stream.id)])
    return bitmovin_api.encoding.encodings.muxings.fmp4.create(encoding_id=encoding.id, fmp4_muxing=muxing)

def _create_drm_config(encoding, muxing, output, output_path):
    #widevine_drm = CencWidevine(pssh=DRM_WIDEVINE_PSSH)
    #playready_drm = CencPlayReady(la_url=DRM_FAIRPLAY_LAURL)
    fairplay_drm = CencFairPlay(iv=DRM_FAIRPLAY_IV,uri=DRM_FAIRPLAY_URI)
    #cenc_drm = CencDrm(outputs=[_build_encoding_output(output=output, output_path=output_path)], key=DRM_KEY, kid=DRM_WIDEVINE_KID, play_ready=playready_drm, widevine=widevine_drm, fair_play=fairplay_drm)
    cenc_drm = CencDrm(outputs=[_build_encoding_output(output=output, output_path=output_path)], key=DRM_KEY, fair_play=fairplay_drm)
    return bitmovin_api.encoding.encodings.muxings.fmp4.drm.cenc.create(encoding_id=encoding.id, muxing_id=muxing.id, cenc_drm=cenc_drm)

def _create_default_dash_manifest(encoding, output, output_path):
    dash_manifest_default = DashManifestDefault(encoding_id=encoding.id, manifest_name="stream.mpd", version=DashManifestDefaultVersion.V1, outputs=[_build_encoding_output(output, output_path)])
    return bitmovin_api.encoding.manifests.dash.default.create(dash_manifest_default=dash_manifest_default)

def _create_default_hls_manifest(encoding, output, output_path):
    hls_manifest_default = HlsManifestDefault(encoding_id=encoding.id, outputs=[_build_encoding_output(output, output_path)], name="master.m3u8", manifest_name="master.m3u8", version=HlsManifestDefaultVersion.V1)
    return bitmovin_api.encoding.manifests.hls.default.create(hls_manifest_default=hls_manifest_default)

def _build_encoding_output(output, output_path):
    acl_entry = AclEntry(permission=AclPermission.PUBLIC_READ)
    return EncodingOutput(output_path=_build_absolute_path(relative_path=output_path), output_id=output.id, acl=[acl_entry])

def _build_absolute_path(relative_path):
    return path.join(S3_OUTPUT_BASE_PATH, EXAMPLE_NAME, relative_path)

def _execute_encoding(encoding, start_encoding_request):
    bitmovin_api.encoding.encodings.start(encoding_id=encoding.id, start_encoding_request=start_encoding_request)
    task = _wait_for_enoding_to_finish(encoding_id=encoding.id)
    while task.status not in [Status.FINISHED, Status.ERROR]:
        task = _wait_for_enoding_to_finish(encoding_id=encoding.id)
    if task.status == Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("Encoding failed")
    print("Encoding finished successfully")

def _wait_for_enoding_to_finish(encoding_id):
    time.sleep(5)
    task = bitmovin_api.encoding.encodings.status(encoding_id=encoding_id)
    print(f"Encoding status is {task.status} (progress: {task.progress} %)")
    return task

def _log_task_errors(task):
    if task is None:
        return
    filtered = [msg for msg in task.messages if msg.type == MessageType.ERROR]
    for message in filtered:
        print(message.text)

if __name__ == '__main__':
    main()

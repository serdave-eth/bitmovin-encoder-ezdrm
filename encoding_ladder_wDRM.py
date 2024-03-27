import time
from datetime import datetime
from os import path
#from bitmovin_api_sdk import AacAudioConfiguration, AclEntry, AclPermission, BitmovinApi, \
#    BitmovinApiLogger, CodecConfiguration, DashManifest, DashManifestDefault, \
#    DashManifestDefaultVersion, Encoding, EncodingOutput, Fmp4Muxing, H264VideoConfiguration, \
#    HlsManifest, HlsManifestDefault, HlsManifestDefaultVersion, HttpInput, Input, ManifestGenerator, \
#    ManifestResource, MessageType, MuxingStream, Output, PresetConfiguration, S3Output, \
#    StartEncodingRequest, Status, Stream, StreamInput, StreamSelectionMode, Task
from bitmovin_api_sdk import *

# Hardcoded configuration parameters
BITMOVIN_API_KEY = ""
HTTP_INPUT_HOST = ""
HTTP_INPUT_FILE_PATH = "" #when you get the shareable link from dropbox, everything from the backslash onwards should go here. Change dl=0 to dl=1
S3_OUTPUT_BUCKET_NAME = ""
S3_OUTPUT_ACCESS_KEY = "" # When you set up the S3 bucket, make sure that programmatic access is enabled. Once it is you can get the access key and secret key.
S3_OUTPUT_SECRET_KEY = ""
#S3_OUTPUT_BASE_PATH = "output" # Make sure you have no back slash here
DRM_KEY = ""
DRM_FAIRPLAY_IV = ""
DRM_FAIRPLAY_URI = ""
DRM_WIDEVINE_KID = "" #EZDRM Widevine KID Hex
DRM_WIDEVINE_PSSH = "" #EZDRM Widevine PSSH
DRM_FAIRPLAY_LAURL = ""
EXAMPLE_NAME = "" # This is the name of the folder that will be added to the output S3 bucket
# Generate a unique suffix for the output path
timestamp_suffix = datetime.now().strftime("%Y%m%d%H%M%S")

S3_OUTPUT_BASE_PATH = f"output/{EXAMPLE_NAME}_{timestamp_suffix}/"
bitmovin_api = BitmovinApi(api_key=BITMOVIN_API_KEY, logger=BitmovinApiLogger())

def main():
    encoding = _create_encoding(
        name=EXAMPLE_NAME,
        description="Encoding with HLS and DASH default manifests with multiple representations"
    )

    http_input = _create_http_input(host=HTTP_INPUT_HOST)
    output = _create_s3_output(
        bucket_name=S3_OUTPUT_BUCKET_NAME,
        access_key=S3_OUTPUT_ACCESS_KEY,
        secret_key=S3_OUTPUT_SECRET_KEY
    )

    video_configurations = [
        _create_h264_video_configuration(width=1280, height=720, bitrate=3000000),
        _create_h264_video_configuration(width=1280, height=720, bitrate=4608000),
        _create_h264_video_configuration(width=1920, height=1080, bitrate=6144000),
        _create_h264_video_configuration(width=1920, height=1080, bitrate=7987200),
    ]

    for config in video_configurations:
        video_stream = _create_stream(encoding=encoding, encoding_input=http_input, input_path=HTTP_INPUT_FILE_PATH, codec_configuration=config)
        video_muxing = _create_fmp4_muxing(encoding=encoding, stream=video_stream)
        _create_drm_config(encoding=encoding, muxing=video_muxing, output=output, output_path=f"video")

    audio_configurations = [
        _create_aac_audio_configuration(bitrate=192000),
        _create_aac_audio_configuration(bitrate=64000),
    ]

    for config in audio_configurations:
        audio_stream = _create_stream(encoding=encoding, encoding_input=http_input, input_path=HTTP_INPUT_FILE_PATH, codec_configuration=config)
        audio_muxing = _create_fmp4_muxing(encoding=encoding, stream=audio_stream)
        _create_drm_config(encoding=encoding, muxing=audio_muxing, output=output, output_path=f"audio")

    dash_manifest = _create_default_dash_manifest(encoding=encoding, output=output, output_path="")
    #hls_manifest = _create_default_hls_manifest(encoding=encoding, output=output, output_path="")

    #start_encoding_request = StartEncodingRequest(manifest_generator=ManifestGenerator.V2, vod_dash_manifests=[ManifestResource(manifest_id=dash_manifest.id)], vod_hls_manifests=[ManifestResource(manifest_id=hls_manifest.id)])
    start_encoding_request = StartEncodingRequest(
        manifest_generator=ManifestGenerator.V2,
        vod_dash_manifests=[ManifestResource(manifest_id=dash_manifest.id)],
        #vod_hls_manifests=[ManifestResource(manifest_id=hls_manifest.id)]
    )
    _execute_encoding(encoding=encoding, start_encoding_request=start_encoding_request)

def _create_encoding(name, description):
    encoding = Encoding(name=name, description=description)
    return bitmovin_api.encoding.encodings.create(encoding=encoding)

def _create_http_input(host):
    http_input = HttpInput(host=host)
    return bitmovin_api.encoding.inputs.http.create(http_input=http_input)

def _create_s3_output(bucket_name, access_key, secret_key):
    s3_output = S3Output(bucket_name=bucket_name, access_key=access_key, secret_key=secret_key)
    return bitmovin_api.encoding.outputs.s3.create(s3_output=s3_output)

def _create_h264_video_configuration(width, height, bitrate):
    config = H264VideoConfiguration(name=f"H.264 {height}p", width=width, height=height, bitrate=bitrate, preset_configuration=PresetConfiguration.VOD_STANDARD)
    return bitmovin_api.encoding.configurations.video.h264.create(h264_video_configuration=config)

def _create_aac_audio_configuration(bitrate):
    config = AacAudioConfiguration(name=f"AAC {bitrate // 1000} Kbps", bitrate=bitrate)
    return bitmovin_api.encoding.configurations.audio.aac.create(aac_audio_configuration=config)

def _create_stream(encoding, encoding_input, input_path, codec_configuration):
    #stream_input = StreamInput(input_id=encoding_input)
    stream_input = StreamInput(input_id=encoding_input.id, input_path=input_path, selection_mode=StreamSelectionMode.AUTO)
    stream = Stream(input_streams=[stream_input], codec_config_id=codec_configuration.id)
    return bitmovin_api.encoding.encodings.streams.create(encoding_id=encoding.id, stream=stream)

def _create_drm_config(encoding, muxing, output, output_path):
    widevine_drm = CencWidevine(pssh=DRM_WIDEVINE_PSSH)
    #playready_drm = CencPlayReady(la_url=DRM_FAIRPLAY_LAURL)
    #fairplay_drm = CencFairPlay(iv=DRM_FAIRPLAY_IV,uri=DRM_FAIRPLAY_URI)
    cenc_drm = CencDrm(outputs=[_build_encoding_output(output=output, output_path=output_path)], key=DRM_KEY, kid=DRM_WIDEVINE_KID, widevine=widevine_drm)
    #cenc_drm = CencDrm(outputs=[_build_encoding_output(output=output, output_path=output_path)], key=DRM_KEY, fair_play=fairplay_drm)
    return bitmovin_api.encoding.encodings.muxings.fmp4.drm.cenc.create(encoding_id=encoding.id, muxing_id=muxing.id, cenc_drm=cenc_drm)


#def _create_fmp4_muxing(encoding, output, output_path, stream):
#    muxing_stream = MuxingStream(stream_id=stream.id)
#    muxing = Fmp4Muxing(segment_length=4.0, streams=[muxing_stream], outputs=[_build_encoding_output(output, output_path)])
#    #_create_drm_config(encoding=encoding, muxing=muxing, output=output, output_path=output_path)
#    return bitmovin_api.encoding.encodings.muxings.fmp4.create(encoding_id=encoding.id, fmp4_muxing=muxing)

def _create_fmp4_muxing(encoding, stream):
    muxing = Fmp4Muxing(segment_length=4.0, streams=[MuxingStream(stream_id=stream.id)])
    return bitmovin_api.encoding.encodings.muxings.fmp4.create(encoding_id=encoding.id, fmp4_muxing=muxing)

def _create_default_dash_manifest(encoding, output, output_path):
    dash_manifest_default = DashManifestDefault(encoding_id=encoding.id, manifest_name="stream.mpd", version=DashManifestDefaultVersion.V1, outputs=[_build_encoding_output(output, output_path)])
    return bitmovin_api.encoding.manifests.dash.default.create(dash_manifest_default=dash_manifest_default)

def _create_default_hls_manifest(encoding, output, output_path):
    hls_manifest_default = HlsManifestDefault(encoding_id=encoding.id, outputs=[_build_encoding_output(output, output_path)], name="master.m3u8", manifest_name="master.m3u8", version=HlsManifestDefaultVersion.V1)
    return bitmovin_api.encoding.manifests.hls.default.create(hls_manifest_default=hls_manifest_default)

def _build_encoding_output(output, output_path):
    acl_entry = AclEntry(permission=AclPermission.PUBLIC_READ)
    return EncodingOutput(output_id=output.id, output_path=_build_absolute_path(output_path), acl=[acl_entry])

def _build_absolute_path(relative_path):
    return path.join(S3_OUTPUT_BASE_PATH, EXAMPLE_NAME, relative_path)

def _execute_encoding(encoding, start_encoding_request):
    bitmovin_api.encoding.encodings.start(encoding_id=encoding.id, start_encoding_request=start_encoding_request)
    task = _wait_for_encoding_to_finish(encoding_id=encoding.id)

    while task.status not in [Status.FINISHED, Status.ERROR]:
        task = _wait_for_encoding_to_finish(encoding_id=encoding.id)

    if task.status == Status.ERROR:
        _log_task_errors(task=task)
        raise Exception("Encoding failed")

    print("Encoding finished successfully")

def _wait_for_encoding_to_finish(encoding_id):
    time.sleep(5)  # Wait for 5 seconds before checking the status
    task = bitmovin_api.encoding.encodings.status(encoding_id=encoding_id)
    print(f"Encoding status is {task.status} (progress: {task.progress}%)")
    return task

def _log_task_errors(task):
    if task and task.messages:
        error_messages = [message for message in task.messages if message.type == MessageType.ERROR]
        for message in error_messages:
            print(message.text)

if __name__ == '__main__':
    main()

# Change shebang before running

import uvicorn
from fastapi import FastAPI
from fastapi import File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import os, sys, argparse
import logging
import datetime, time

import requests as rq
from extras.utils import set_cwd_to_location

app = FastAPI()
REQUEST_TIMEOUT = 5
set_cwd_to_location(__file__)

# Utility functions
def generate_big_file(filename, size: int = 100) -> str:
    """
    Create random file with name and
    size in unit MB
    """
    file_path = f"temp/{filename}"
    if os.path.exists(file_path):
        os.remove(file_path)
    with open(f"{file_path}", "wb") as f:
        f.seek(1024 * 1024 * size - 1)
        f.write(str.encode("0"))
    logging.info(f"File: {file_path} generated with size: {size}MB")
    return file_path


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Folder: {path} created")


# API functions
class FileTask(BaseModel):
    ip: str | None = "0.0.0.0"
    port: int | None = 8000
    size: int | None = 100  # MByte


class RemoveFileTask(BaseModel):
    file_path: str


@app.get("/")
async def helloworld():
    return {'status': True}

@app.post("/remove_file/")
async def remove_file(rm_task: RemoveFileTask):
    """
    Remove file from server remotly \n
    Not for end user
    """
    file_path = rm_task.file_path
    try:
        os.remove(file_path)
        logging.info(f"File: {file_path} deleted")
    except FileNotFoundError:
        logging.error(f"File: {file_path} not exist")
        return {"status": f"File: {file_path} not exist"}
    except PermissionError:
        logging.error(f"File: {file_path} no permission to delete file")
        return {"status": f"File: {file_path} no permission to delete file"}
    except Exception as e:
        logging.error(e)
        return {"status": "exeption check log"}
    return {"status": "success"}


@app.post("/upload_speed/")
async def upload_speed(upload_task: FileTask):
    """
    url with default upload size = 100mb \n
    filename is unix time in nanosecond \n
    store file in temp/upload folder \n
    speed unit: Mbit/s
    """
    filename = time.time_ns()
    file_path = generate_big_file(filename, upload_task.size)
    with open(f"{file_path}", "r") as upload_file:
        logging.info(f"Uploading file: {file_path}")
        start_time = time.time_ns()
        try:
            respone = rq.post(
                f"http://{upload_task.ip}:{upload_task.port}/upload",
                files={"file": upload_file},
                timeout=REQUEST_TIMEOUT,
            )
        except rq.Timeout:
            logging.error(f"Upload timeout {upload_task.ip}:{upload_task.port}")
            return {"upload_speed": -1}
        except rq.ConnectionError:
            logging.error(f"Connection error {upload_task.ip}:{upload_task.port}")
            return {"upload_speed": -1}

        end_time = time.time_ns()
    logging.info(f"Temp file: {file_path} removed")
    os.remove(file_path)

    speed = -1
    if respone.status_code == 200:
        speed = upload_task.size * 8 / ((end_time - start_time) / 1e9)
        speed = round(speed, 5)
    # Upload speed is in Mbit/s
    logging.info(f"Upload speed: {speed} Mbit/s")
    return {"upload_speed": speed}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    try:
        file_path = f"temp/upload/{file.filename}"
        with open(file_path, "wb") as f:
            while contents := file.file.read(1024 * 1024):
                f.write(contents)
    except Exception:
        logging.error(f"Error uploading file: {file.filename}")
        return {"message": "There was an error uploading the file"}
    finally:
        logging.info(f"File: {file.filename} uploaded")
        file.file.close()
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Temp file: {file_path} removed")
    return {"message": f"Successfully uploaded {file.filename}"}


@app.post("/download_speed/")
async def download_speed(download_task: FileTask):
    """
    url with default download size = 100mb \n
    filename is unix time in nanosecond \n
    filename is unix time store temporaly in temp/download \n
    speed unit: Mbit/s
    """
    try:
        with rq.get(
            f"http://{download_task.ip}:{download_task.port}/download/{download_task.size}",
            stream=True,
            timeout=REQUEST_TIMEOUT,
        ) as respone:
            # get filename from header
            sv_path = (
                respone.headers["Content-Disposition"].split("=")[1].replace('"', "")
            )
            cl_path = f'temp/download/{sv_path.split("/")[-1]}'

            logging.info(f"Downloading file: {sv_path}")
            start_time = time.time_ns()
            respone.raise_for_status()
            with open(cl_path, "wb") as f:
                for chunk in respone.iter_content(chunk_size=8192):
                    f.write(chunk)
            end_time = time.time_ns()
            logging.info(f"File: {sv_path} downloaded")

            speed = -1
            if respone.status_code == 200:
                size = os.path.getsize(cl_path)
                speed = size / 1024 / 1024 * 8 / ((end_time - start_time) / 1e9)
                speed = round(speed, 5)
            logging.info(f"Download speed: {speed} Mbit/s")
    except rq.Timeout:
        logging.error(f"Download timeout {download_task.ip}:{download_task.port}")
    except rq.ConnectionError:
        logging.error(f"Connection error {download_task.ip}:{download_task.port}")

    try:
        rq.post(
            f"http://{download_task.ip}:{download_task.port}/remove_file",
            json={"file_path": sv_path},
            timeout=REQUEST_TIMEOUT,
        )
        os.remove(cl_path)
        logging.info(f"Temp file: {cl_path} removed")
    except rq.Timeout:
        logging.error(f"Remove file timeout {download_task.ip}:{download_task.port}")
    except rq.ConnectionError:
        logging.error(f"Connection error {download_task.ip}:{download_task.port}")
    except UnboundLocalError:
        logging.error(
            f"File at server {download_task.ip}:{download_task.port}: {sv_path} not exist"
        )
    except FileNotFoundError:
        logging.error(f"File at client: {cl_path} not exist")

    return {"download_speed": speed}


@app.get("/download/{size}")
async def download(size: int = 100):
    """
    Internal API for download speed test \n
    Not for user \n
    return file respone
    """
    filename = time.time_ns()
    file_path = generate_big_file(filename, size)
    return FileResponse(path=file_path, filename=file_path)


class ResponeTimeTask(BaseModel):
    ip: str | None = "0.0.0.0"
    port: int | None = 8000


@app.post("/respone_time")
async def server_respone_time(rpt_task: ResponeTimeTask):
    """
    Step 1: client send request to server with time \n
    Step 2: server recive request and calculate cl to sv time then return sv time and sv to cl time \n
    Step 3: client recive response and calculate time \n
    return server time in milisecond
    """
    cl_current_time = time.time_ns()
    try:
        sv_data = rq.post(
            f"http://{rpt_task.ip}:{rpt_task.port}/sv_respone_time",
            json={"cl_current_time": cl_current_time},
        ).json()
    except rq.Timeout:
        logging.error(f"Respone time timeout {rpt_task.ip}:{rpt_task.port}")
        return {"respone_time": -1}
    except rq.ConnectionError:
        logging.error(f"Connection error {rpt_task.ip}:{rpt_task.port}")
        return {"respone_time": -1}

    cl_to_sv = sv_data["cl_to_sv"]
    sv_current_time = sv_data["sv_current_time"]
    result_time = time.time_ns() - sv_current_time + cl_to_sv
    result_time = round(result_time / 10**6, 5)

    # return in rounded milisecond
    logging.info(f"Respone time: {result_time} ms")
    return {"respone_time": result_time}


class ResponeTimeChainTask(BaseModel):
    cl_current_time: int


@app.post("/sv_respone_time")
async def post_server_respone_time(rp_time: ResponeTimeChainTask):
    """
    Internal API for respone time test \n
    Not for user \n
    """
    sv_current_time = time.time_ns()
    cl_to_sv_latency = time.time_ns() - rp_time.cl_current_time
    logging.info(
        f"cl_to_sv_latency: {cl_to_sv_latency}, sv_current_time: {sv_current_time}"
    )
    return {"cl_to_sv": cl_to_sv_latency, "sv_current_time": sv_current_time}


def main():
    parser = argparse.ArgumentParser(description="simple cli client")

    parser.add_argument("ip", type=str, default="0.0.0.0", help="ip address of server")
    parser.add_argument("port", type=int, default=8000, help="port of server")
    args = parser.parse_args()

    # Create folder for temp file
    mkdir("./temp/download/")
    mkdir("./temp/upload/")
    mkdir("./log")

    # Create logger
    file_handler = logging.FileHandler(
        filename=f'log/{args.ip}:{args.port}_{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.log'
    )
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        handlers=handlers,
    )

    uvicorn.run(app, host=args.ip, port=args.port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # os.remove('temp')
        sys.exit(0)

# api docs: http://0.0.0.0:8001/docs (or ip and port)
# python http_file_transfer.py 0.0.0.0 8000 - or ip and port

#!/usr/bin/env python3

import argparse
import html
import logging
import mimetypes
import os
import posixpath
import re
import subprocess
import urllib
import uuid
from datetime import datetime
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class LoopInfo(Enum):
    OUTER = 1
    INNER = 2
    LEAVE = 3


def get_local_ip():
    def parse_ip(output):
        return re.findall(r"inet\s+(192\.168\.\d+\.\d+)", output)

    def get_ip_from_command(cmd):
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, check=True)
            return parse_ip(result.stdout)
        except subprocess.CalledProcessError:
            pass
        return []

    ip_list = get_ip_from_command(["ifconfig"])
    if ip_list:
        return ip_list[0]

    ip_list = get_ip_from_command(["ip", "addr"])
    if ip_list:
        return ip_list[0]

    return "[::]"


def format_size(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def safe_save_path(path, filename):
    new_filename = filename
    full_path = os.path.join(path, new_filename)
    while os.path.exists(full_path):
        dot = new_filename.rfind(".")
        prefix = new_filename[:dot]
        suffix = new_filename[dot:]
        new_filename = f"{prefix}_{uuid.uuid4()}{suffix}"
        full_path = os.path.join(path, new_filename)
    return full_path


def init_mimetypes():
    if not mimetypes.inited:
        mimetypes.init()
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update(
        {
            ".py": "text/plain",
            ".c": "text/plain",
            ".h": "text/plain",
        }
    )
    return extensions_map


class CustomRequestHandler(BaseHTTPRequestHandler):
    extensions_map = init_mimetypes()

    def log_message(self, format, *args):
        """Disable default HTTP server logging."""
        pass

    def do_GET(self):
        f = self.send_head()
        if f:
            self.wfile.write(f)

    def do_HEAD(self):
        self.send_head()

    def do_POST(self):
        r, info = self.deal_post_data()

        logging.info(info)
        logging.info("uploaded by: {}".format(self.client_address))

        info = info.replace("\n", "<br>")
        result = "Success" if r else "Failed"
        referer = self.headers.get("referer", "/")
        self.send_html_resp(result, info, referer)

    def send_html_resp(self, result, info, referer):
        f = '<!DOCTYPE><html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"><title>{result}</title></head><body><h2>{result}</h2><hr>{info}<br><a href="{referer}">back</a></body>\n</html>'.format(
            result=result, info=info, referer=referer
        )

        f = f.encode("utf-8")
        length = len(f)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.wfile.write(f)

    def deal_post_data(self):
        content_type = self.headers.get("Content-Type", "")
        if not content_type or "boundary=" not in content_type:
            return False, "Content-Type header missing or invalid boundary"
        boundary = content_type.split("boundary=")[1]

        boundary_begin = ("--" + boundary + "\r\n").encode("utf-8")
        boundary_end = ("--" + boundary + "--\r\n").encode("utf-8")

        return_status = True
        return_info = ""
        loop_info = LoopInfo.OUTER

        line = self.rfile.readline()

        while loop_info == LoopInfo.OUTER:
            if line != boundary_begin:
                return_status = False
                return_info += "Content NOT begin with boundary\n"
                break

            line = self.rfile.readline().decode("utf-8").rstrip("\r\n")
            filename_match = re.findall(r'filename="(.*)"', line)
            if not filename_match:
                return_status = False
                return_info += "Can't find out file name...\n"
                loop_info = LoopInfo.LEAVE
                break
            fn = filename_match[0]
            path = self.translate_path(self.path)
            filename = safe_save_path(path, fn)

            line = self.rfile.readline()
            line = self.rfile.readline()
            loop_info = LoopInfo.INNER

            try:
                with open(filename, "wb") as f:
                    buf = bytearray(8192)
                    while loop_info == LoopInfo.INNER:
                        line = self.rfile.readline()
                        if line == boundary_begin:
                            loop_info = LoopInfo.OUTER
                            if buf:
                                f.write(buf)
                            break
                        elif line == boundary_end:
                            loop_info = LoopInfo.LEAVE
                            if buf:
                                f.write(buf)
                            break
                        else:
                            buf.extend(line)
                            if len(buf) > 8192:
                                f.write(buf)
                                buf.clear()
            except Exception as e:
                loop_info = LoopInfo.LEAVE
                return_status = False
                return_info += f"Exception: {e}\n"
            return_info += filename
        return (return_status, return_info)

    def send_head(self):
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith("/"):
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in ["index.html", "index.htm"]:
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            with open(path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                fs = os.fstat(f.fileno())
                self.send_header("Content-Length", str(fs[6]))
                self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
                self.end_headers()
                return f.read()
        except IOError:
            self.send_error(404, "File not found")
            return None

    def list_directory(self, path):
        try:
            file_list = os.listdir(path)
        except os.error:
            self.send_error(404, "没有权限列出目录")
            return None

        file_list.sort(key=lambda a: a.lower())
        displaypath = html.escape(urllib.parse.unquote(self.path))

        f = f"""
        <!DOCTYPE HTML>
        <html>
        <head>
        <meta charset="utf-8">
        <title>目录列表 - {displaypath}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .folder {{ color: #0073e6; font-weight: bold; }}
        </style>
        </head>
        <body>
        <h2>目录列表: {displaypath}</h2>
        <form ENCTYPE="multipart/form-data" method="post">
            <input name="file" type="file" multiple>
            <input type="submit" value="上传文件">
        </form>
        <hr>
        <table>
            <tr>
                <th>名称</th>
                <th>大小</th>
                <th>修改时间</th>
            </tr>
        """

        for name in file_list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
                size = "-"
                cls = "folder"
            else:
                size = os.path.getsize(fullname)
                size = format_size(size)
                cls = "file"

            mtime = os.path.getmtime(fullname)
            mtime = datetime.fromtimestamp(mtime).isoformat(timespec="seconds")
            f += f"""
            <tr>
                <td><a class="{cls}" href="{urllib.parse.quote(linkname)}">{html.escape(displayname)}</a></td>
                <td>{size if size != '-' else '-'}</td>
                <td>{mtime}</td>
            </tr>
            """

        f += "</table><hr></body></html>"
        f = f.encode("utf-8")
        length = len(f)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        path = path.split("?", 1)[0]
        path = path.split("#", 1)[0]
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = path.split("/")
        words = filter(None, words)
        path = os.getcwd()
        for word in words:
            _, word = os.path.splitdrive(word)
            _, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        return path

    def guess_type(self, path):
        _, ext = posixpath.splitext(path)
        ext_lower = ext.lower()
        return self.extensions_map.get(ext_lower, "application/octet-stream")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTP File Server")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()

    port = args.port
    ip_addr = get_local_ip()

    logging.basicConfig(level=logging.INFO)
    with ThreadingHTTPServer(("", port), CustomRequestHandler) as httpd:
        logging.info(f"Serving on http://{ip_addr}:{port}")
        httpd.serve_forever()

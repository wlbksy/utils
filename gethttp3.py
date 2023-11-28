#!/usr/bin/env python3


import os
import posixpath
import http.server
import urllib
import html
import shutil
import mimetypes
import re
import sys


class SimpleHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP request handler with GET/HEAD/POST commands.
    This serves files from the current directory and any of its
    subdirectories.  The MIME type for files is determined by
    calling the .guess_type() method. And can reveive file uploaded
    by client.
    The GET/HEAD/POST requests are identical except that the HEAD
    request omits the actual contents of the file.
    """

    if not mimetypes.inited:
        mimetypes.init()  # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update(
        {
            "": "application/octet-stream",  # Default
            ".py": "text/plain",
            ".c": "text/plain",
            ".h": "text/plain",
        }
    )

    def do_GET(self):
        """Serve a GET request."""
        f = self.send_head()
        if f:
            self.wfile.write(f)

    def do_HEAD(self):
        """Serve a HEAD request."""
        f = self.send_head()

    def do_POST(self):
        """Serve a POST request."""
        r, info = self.deal_post_data()

        result = "Success" if r else "Failed"

        print(info)
        print("uploaded by:{}".format(self.client_address))
        info = info.replace("\n", "<br>")
        f = (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
            + '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
            + '<title>{}</title></head><body><h2>{}</h2><hr>{}<br><a href="{}">back</a></body>\n</html>'.format(
                result, result, info, self.headers["referer"]
            )
        )

        f = f.encode("utf-8")
        length = len(f)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        self.wfile.write(f)

    def deal_post_data(self):
        boundary = self.headers["Content-Type"].split("=")[1]

        boundary_begin = ("--" + boundary + "\r\n").encode("utf-8")
        boundary_end = ("--" + boundary + "--\r\n").encode("utf-8")

        return_status = True
        return_info = "\n"
        outer = 1
        inner = 2
        leave = 3
        loop_info = outer  # 1: outer loop, 2: inner_loop, 3: leave and return

        line = self.rfile.readline()

        while loop_info == outer:
            if line != boundary_begin:
                return_status = False
                return_info += "Content NOT begin with boundary\n"
                break

            line = self.rfile.readline().decode("utf-8").rstrip("\r\n")
            # print(line)
            filename = re.findall(r'filename="(.*)"', line)[0]
            name = filename
            if not filename:
                return_status = False
                return_info += "Can't find out file name...\n"
                loop_info = leave
                break
            path = self.translate_path(self.path)
            filename = os.path.join(path, filename)
            # if filename already exists
            dup_cnt = 1
            while os.path.exists(filename):
                dot = name.rfind(".")
                prefix = name[:dot]
                suffix = name[dot:]
                filename = "{}_{}{}".format(prefix, dup_cnt, suffix)
                filename = os.path.join(path, filename)
                dup_cnt += 1

            line = self.rfile.readline()
            line = self.rfile.readline()
            loop_info = inner

            try:
                buf = b""
                with open(filename, "wb") as f:
                    while loop_info == inner:
                        line = self.rfile.readline()
                        if line == boundary_begin:
                            loop_info = outer
                            f.write(buf[:-2])
                            break
                        elif line == boundary_end:
                            loop_info = leave
                            # post 数据的实际内容, 在 boundary_end 之前那一行就已经结束了
                            # 而这一行数据后面紧跟的 '\r\n' 只是为了区分接下来的 boundary_end
                            # 因此在把数据写如文件的时候, 要把这个多余的 '\r\n' 去掉
                            f.write(buf[:-2])
                            break
                        else:
                            if len(buf) > 1024:
                                f.write(buf)
                                buf = b""
                            buf += line
            except:
                loop_info = leave
                return_status = False
                return_info += "Exception!\n"
            return_info += filename + "\n"
        return (return_status, return_info)

    def send_head(self):
        """Common code for GET and HEAD commands.
        This sends the response code and MIME headers.
        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.
        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith("/"):
                # redirect browser - doing basically what apache does
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
            f = open(path, "rb")
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        data = f.read()
        f.close()

        return data

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).
        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().
        """
        try:
            file_list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        file_list.sort(key=lambda a: a.lower())
        displaypath = html.escape(urllib.parse.unquote(self.path))

        f = (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"'
            + '"http://www.w3.org/TR/html4/strict.dtd"><html><head>'
            + '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
            + "<title>Directory listing for {}</title>".format(displaypath)
            + "</head><body><h2>Directory listing for {}</h2>".format(displaypath)
            + '<form ENCTYPE="multipart/form-data" method="post"><input name="file" type="file"'
            + ' multiple="multiple"/><input type="submit" value="upload"/></form><hr><ul>'
        )

        for name in file_list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f += '<li><a href="{}">{}</a>'.format(
                urllib.parse.quote(linkname), html.escape(displayname)
            )
        f += "</ul><hr></body></html>"

        f = f.encode("utf-8")
        length = len(f)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.
        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)
        """
        # abandon query parameters
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
        """Guess the type of a file.
        Argument is a PATH (a filename).
        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.
        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.
        """

        _, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map[""]


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    http.server.test(SimpleHTTPRequestHandler, http.server.HTTPServer, port=port)

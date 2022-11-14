#-- coding: utf-8 -- 

import urllib

import urllib.parse
import http.cookies
import os
import os.path
import sys
import threading
import json
import re
import copy
import datetime
#import io
import hashlib
import tarfile
import gzip
import time

import inspect

import asyncio
# import aioprocessing

from collections import namedtuple
from wsgiref.util import FileWrapper

import mimetypes
import cgi

httpcodes = [
    ("CONTINUE", 100),
    ("SWITCHING_PROTOCOLS", 101),
    ("PROCESSING", 102),
    ("OK", 200),
    ("CREATED", 201),
    ("ACCEPTED", 202),
    ("NON_AUTHORITATIVE_INFORMATION", 203),
    ("NO_CONTENT", 204),
    ("RESET_CONTENT", 205),
    ("PARTIAL_CONTENT", 206),
    ("MULTI_STATUS", 207),
    ("IM_USED", 226),
    ("MULTIPLE_CHOICES", 300),
    ("MOVED_PERMANENTLY", 301),
    ("FOUND", 302),
    ("SEE_OTHER", 303),
    ("NOT_MODIFIED", 304),
    ("USE_PROXY", 305),
    ("TEMPORARY_REDIRECT", 307),
    ("BAD_REQUEST", 400),
    ("UNAUTHORIZED", 401),
    ("PAYMENT_REQUIRED", 402),
    ("FORBIDDEN", 403),
    ("NOT_FOUND", 404),
    ("METHOD_NOT_ALLOWED", 405),
    ("NOT_ACCEPTABLE", 406),
    ("PROXY_AUTHENTICATION_REQUIRED", 407),
    ("REQUEST_TIMEOUT", 408),
    ("CONFLICT", 409),
    ("GONE", 410),
    ("LENGTH_REQUIRED", 411),
    ("PRECONDITION_FAILED", 412),
    ("REQUEST_ENTITY_TOO_LARGE", 413),
    ("REQUEST_URI_TOO_LONG", 414),
    ("UNSUPPORTED_MEDIA_TYPE", 415),
    ("REQUESTED_RANGE_NOT_SATISFIABLE", 416),
    ("EXPECTATION_FAILED", 417),
    ("UNPROCESSABLE_ENTITY", 422),
    ("LOCKED", 423),
    ("FAILED_DEPENDENCY", 424),
    ("UPGRADE_REQUIRED", 426),
    ("PRECONDITION_REQUIRED", 428),
    ("TOO_MANY_REQUESTS", 429),
    ("REQUEST_HEADER_FIELDS_TOO_LARGE", 431),
    ("INTERNAL_SERVER_ERROR", 500),
    ("NOT_IMPLEMENTED", 501),
    ("BAD_GATEWAY", 502),
    ("SERVICE_UNAVAILABLE", 503),
    ("GATEWAY_TIMEOUT", 504),
    ("HTTP_VERSION_NOT_SUPPORTED", 505),
    ("INSUFFICIENT_STORAGE", 507),
    ("NOT_EXTENDED", 510),
    ("NETWORK_AUTHENTICATION_REQUIRED", 511),
]

httpcodes_s2i = dict(httpcodes)
httpcodes_i2s = dict([(i, s) for s, i in httpcodes])

def anno_str(anno):
    
    if type(anno) == type:
        return anno.__name__

    return str(anno)
    
def trim(docstring):
    
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

class HttpResponse(object):
    
    def __init__(self, status, reason, headers, body):

        self.exc_info = None

        self.status = status if status else httpcodes_s2i[reason]
        self.reason = reason if reason else httpcodes_i2s[status]
        self.headers = list(headers.items()) if type(headers) == dict else headers
        
        if body is None:
            body = b''

        if type(body) == str:
            body = body.encode('utf-8')
        elif type(body) == bytes:
            body = body
        else :
            body = json.dumps(body, ensure_ascii=False, default=str).encode('utf-8')
        
        self.body = body

        return

    def headstruct(self):
        return ('%s %s' % (self.status, self.reason), self.headers, self.exc_info)
        
        

class HttpWebSocket(HttpResponse):
    def __init__(self, **kwargs ):
        self.wsc_args = kwargs
        super().__init__(200, None, [], '')
        return

class HttpOK(HttpResponse):
    def __init__(self, headers=[], body=''):
        super().__init__(200, None, headers, body)
        return


class HttpFile(HttpResponse):
    
    def __init__( self, headers=[], filereader=None ):
        super().__init__(200, None, headers,'')        
        self.body = filereader()

        return
        

class HttpMemFile(HttpResponse):
    
    def __init__( self, filename, filecnt ):
    
        headers = []
        filename = urllib.parse.quote(filename.encode('utf-8'))
        headers.append( ('Content-Disposition',"attachment; filename* = UTF-8''"+filename) )
        
        super().__init__(200, None, headers, filecnt)
        
        return


class HttpBadRequest(HttpResponse):
    def __init__(self, headers=[], body=''):
        super().__init__(400, None, headers, body)
        return

class HttpLockedResource(HttpResponse):
    def __init__(self, headers=[], body=''):
        super().__init__(423, None, headers, body)
        return


class HttpNotFound(HttpResponse):
    def __init__(self, headers=[], body=''):
        super().__init__(404, None, headers, body)
        return


class HttpForbidden(HttpResponse):
    def __init__(self, headers=[], body=''):
        super().__init__(403, None, headers, body)
        return


class HttpRedirect(HttpResponse):
    def __init__(self, redirect_url):
        self.redirect_url = redirect_url
        headers = {'Location': redirect_url}
        super().__init__(302, None, headers, '')
        return


class HttpXRedirect(HttpResponse):
    def __init__(self, redirect_url):
        self.redirect_url = redirect_url
        headers = {'X-Accel-Redirect': redirect_url}
        super().__init__(301, None, headers, '')
        return


class HttpInternalServerError(HttpResponse):
    def __init__(self, exc_info=None, body=''):
        self.exc_info = sys.exc_info() if exc_info == None else exc_info
        super().__init__(500, None, [], body)
        return

class HttpMemTarFile(HttpResponse):
    
    def __init__(self, tarname='', files=[]):
        
        headers = []
        if tarname :
            tarname = urllib.parse.quote(tarname.encode('utf-8'))
            headers.append( ('Content-Disposition',"attachment; filename* = UTF-8''"+tarname) )
            
        super().__init__(200, None, headers, '')
        
        self.body = self.gen()
        
        self.files = files
        
        for tarname, filecnt in self.files :
            
            if type(tarname) != str :
                raise Exception('tarname must be str')
                
            if type(filecnt) != bytes :
                raise Exception('filecnt must be bytes')
        
        return

    def gen(self):
        
        for tarname, filecnt in self.files :
            
            t = tarfile.TarInfo(tarname)
            t.size = len(filecnt)
            
            yield t.tobuf(0,'utf-8','surrogateescape')
            
            yield filecnt
            
            blocks, remainder = divmod(t.size, tarfile.BLOCKSIZE)
            if remainder > 0:
                yield tarfile.NUL * (tarfile.BLOCKSIZE - remainder)
            
        return
        
class HttpTarFile(HttpResponse):
    
    def __init__(self, tarname='', files=[]):
        
        headers = []
        if tarname :
            tarname = urllib.parse.quote(tarname.encode('utf-8'))
            headers.append( ('Content-Disposition',"attachment; filename* = UTF-8''"+tarname) )
            
        super().__init__(200, None, headers, '')
        self.body = self.gen()
        
        self.files = files
        
        return
    
    def gen(self):
        
        for tarname, filepath in self.files :
            
            with open( filepath, 'rb' ) as fp:
                
                t = tarfile.TarInfo(tarname)
                
                fp.seek(0,2)
                t.size = size = fp.tell()
                
                yield t.tobuf(0,'utf-8','surrogateescape')
                
                fp.seek(0,0)
                r = True
                while r:
                    r = fp.read(1024*1024)
                    yield r
                    
                blocks, remainder = divmod(t.size, tarfile.BLOCKSIZE)
                if remainder > 0:
                    yield tarfile.NUL * (tarfile.BLOCKSIZE - remainder)
            
        return


import collections
class AttrDict(collections.UserDict):

    def __missing__(self, key):
        return ''
    
    def __getattr__( self, key ):
        return self[key]
    

class WSClient(object):
    
    def __init__( self ):
        # self.sq = aioprocessing.AioQueue()
        self.rq = asyncio.Queue()
        
    def send( self, msg ):
        self.sq.put( msg )
    
    async def recv( self ):
        r = await self.rq.get()
        return r
    
class WsgiRouter(object):

    def __init__( self ):
        self.rules = []
        self.re_rules = []
        return
    
    def urlre( self, url ):
        return lambda f: self.add_urlre( url, f )
    
    def add_urlre( self, url, f ):
        self.re_rules.append( (url, f.__name__) )
        return f
        
    def url( self, url ):
        return lambda f: self.add_url( url, f )
    
    def add_url( self, url, f ):
        self.rules.append( (url, f.__name__) )
        return f
        
def router():
    return WsgiRouter()
    
class WsgiServer(object):
    
    Response = HttpResponse
    Redirect = HttpRedirect
    XRedirect = HttpXRedirect
    File = HttpFile
    WebSocket = HttpWebSocket
    TarFile = HttpTarFile
    MemTarFile = HttpMemTarFile
    
    OK = HttpOK
    BadRequest = HttpBadRequest
    NotFound = HttpNotFound
    Forbidden = HttpForbidden
    InternalServerError = HttpInternalServerError
    
    router = WsgiRouter()
    
    def __init__( self ):
        
        self.rules = [ (m[3:].replace('__', '/'), m) for m in dir(self) if m.startswith('url__') ]
        self.rules = dict(self.rules)
        
        self.rules.update( dict(self.router.rules) )
        
        self.re_rules = [ (re.compile(urlre), wi) for urlre, wi in self.router.re_rules ]
        
        return
        
    def __call__( self, environ, start_response ):
        return copy.copy(self).process( environ, start_response )
    
    @classmethod
    def generate_doc( cls ):
        
        apis = [ m for m in dir(cls) if m.startswith('url__') ]
        
        for m in apis :
            
            mf = getattr(cls, m)
            url = m[3:].replace('__', '/')
            spec = inspect.getfullargspec(mf)

            argnames = spec.args + spec.kwonlyargs

            defaults = [] if spec.defaults is None else [(True, i) for i in spec.defaults]
            defaults = [(False, None)] * (len(spec.args) - len(defaults)) + defaults

            kwdefaults = [] if spec.kwonlydefaults is None else [(True, i) for i in spec.kwonlydefaults]
            kwdefaults = [(False, None)] * (len(spec.kwonlyargs) - len(kwdefaults)) + kwdefaults

            hasdefaults, defaultvalues = zip(*(defaults + kwdefaults))

            annotations = [spec.annotations.get(a, '') for a in argnames]
            annotations = [anno_str(a) for a in annotations]

            args = zip(argnames, hasdefaults, defaultvalues, annotations)
            args = list(args)
            if args and args[0][0] == 'self':
                args = args[1:]

            anno_return = spec.annotations.get('return', '')

            apidoc = {
                'api': url,
                'args': args,
                'return': anno_str(anno_return),
                'doc': trim(mf.__doc__),
            }

            yield apidoc

            if anno_return != 'websocket':
                continue

            mf = getattr(cls, 'ws' + m[3:], None)

            if mf == None:
                continue

            spec = inspect.getfullargspec(mf)
            ws_spec = spec.annotations.get('return', '')

            if type(ws_spec) != dict:
                continue

            if 'prefix' not in ws_spec or 'api' not in ws_spec:
                continue

            if type(ws_spec['api']) not in (list, tuple, set):
                continue

            for wsapi in [wsapi for wsapi in ws_spec['api'] if type(wsapi) == str]:

                mf = getattr(cls, ws_spec['prefix'] + wsapi, None)
                if mf is None:
                    continue

                spec = inspect.getfullargspec(mf)

                argnames = spec.args + spec.kwonlyargs

                defaults = [] if spec.defaults is None else [(True, i) for i in spec.defaults]
                defaults = [(False, None)] * (len(spec.args) - len(defaults)) + defaults

                kwdefaults = [] if spec.kwonlydefaults is None else [(True, i) for i in spec.kwonlydefaults]
                kwdefaults = [(False, None)] * (len(spec.kwonlyargs) - len(kwdefaults)) + kwdefaults

                hasdefaults, defaultvalues = zip(*(defaults + kwdefaults))

                annotations = [spec.annotations.get(a, '') for a in argnames]
                annotations = [anno_str(a) for a in annotations]

                args = zip(argnames, hasdefaults, defaultvalues, annotations)
                args = list(args)
                if args and args[0][0] == 'self':
                    args = args[1:]

                anno_return = spec.annotations.get('return', '')

                apidoc = {
                    'api': url + ' :: ' + wsapi,
                    'args': args,
                    'return': anno_str(anno_return),
                    'doc': trim(mf.__doc__),
                }

                yield apidoc

        return
    
    def process( self, environ, start_response ):
        
        if 'EWSGICTRL' in environ:
            w, args = self.ctrl_entry( environ )
            resp = w(*args)
            start_response( *resp.headstruct() )
            return resp.body
        
        websocket = bool( 'HTTP_SEC_WEBSOCKET_VERSION' in environ )
        
        w, args = self.http_entry( environ )
        
        resp = w(*args)
        
        # if websocket and isinstance( resp, HttpWebSocket ):
        
        #     w, args = self.ws_entry( environ, resp )
        #     resp = w(*args)
            
        #     return []
        
        start_response( *resp.headstruct() )
    
        return resp.body
    
    @staticmethod
    def read_input( environ ):
        
        r = environ['wsgi.input'].read()
        if r.startswith(b'\x1f\x8b'):
            r = gzip.decompress(r)
        
            environ['ewsgi.content'] = ('json','gz')
        
        return r
    
    def http_entry( self, environ ):
        # print(".......",environ)
        self.env = AttrDict(environ)
        self.host = environ['HTTP_HOST']
        self.path = environ['PATH_INFO']
        self.user_agent = environ.get('HTTP_USER_AGENT','')
        
        self.session = AttrDict({})
        self.cookie = AttrDict({})
        
        try :
            self.session = AttrDict(json.loads( environ['USER_SESSION'] ))
        except :
            pass
        
        try :
            c = http.cookies.SimpleCookie()
            c.load( environ['HTTP_COOKIE'] )
            c = [ (ci.key.lower(), ci.value) for ci in c.values() ]
            self.cookie = AttrDict(c)
        except :
            c = []
        
        
        args = {}
        argsrcs = {}
        
        path = environ['PATH_INFO']
        wi = self.rules.get(path)
        w = None
        
        if wi == None :
            
            for resurl, wi in self.re_rules :
                gs = resurl.match(path)
                if gs :
                    args.update(gs.groupdict())
                    break
            else :
                wi = None
        
        if wi :
            w = getattr( self, wi, None )
        
        
        if w :
            
            qs = environ['QUERY_STRING'].split('&')
            qs = [ x.split('=',1) for x in qs if x ]
            qs = [ (k, urllib.parse.unquote_plus(v)) for k, v in qs if not k.startswith('_') ]
            qs = dict(qs)
            
            args.update(qs)
            argsrcs.update( dict.fromkeys(args.keys(), 'qs') )
            
            if environ['REQUEST_METHOD'] == 'POST' :
                
                ctype, pdict = cgi.parse_header( environ.get('HTTP_CONTENT_TYPE', environ.get('CONTENT_TYPE','')) )
                
                if ctype.startswith('application/x-www-form-urlencoded') :
                    self.env['ewsgi.content'] = ('form','urlencoded')
                    pd = environ['wsgi.input'].read().decode('utf-8')
                    pd = pd.split('&')
                    pd = [ x.split('=',1) for x in pd if x ]
                    pd = [ (k, urllib.parse.unquote_plus(v)) for k, v in pd ]
                    pd = dict(pd)
                
                    args.update(pd)
                    argsrcs.update( dict.fromkeys(pd.keys(), 'qs') )
            
                elif ctype.startswith('multipart/form-data') :
                    self.env['ewsgi.content'] = ('form','multipart')
                    pd = self.parse_multipart(environ['wsgi.input'], pdict, environ)
                    args.update(pd)
                    argsrcs.update( dict.fromkeys(pd.keys(), 'qs') )
                
                elif ctype.startswith('application/json') or ctype.startswith('text/plain') :
                    self.env['ewsgi.content'] = ('json','text')
                    #pd = environ['wsgi.input'].read().decode('utf-8')
                    pd = self.read_input(self.env).decode('utf-8')
                    pd = json.loads( pd )
                    
                    if type(pd) == dict :
                        args.update( pd )
                        argsrcs.update( dict.fromkeys(pd.keys(), 'json') )
                    else :
                        args['_json_arg'] = pd
                        argsrcs.update( {'_json_arg':'json'} )
                    
            return ( self.http_cgi, (w, args, argsrcs, c) )

        return ( self.http_notfound, () )
    
    def ctrl_entry( self, environ ):
        
        args = {}
        
        funcname = environ['EWSGICTRL']
        w = getattr( self, 'srvcmd_'+funcname, None )
        
        if w :
            
            if environ['REQUEST_METHOD'] == 'POST' :
                
                self.env['ewsgi.content'] = ('json','text')
                pd = self.read_input(self.env).decode('utf-8')
                pd = json.loads( pd )
                
                if type(pd) == dict :
                    args.update( pd )
                    argsrcs.update( dict.fromkeys(pd.keys(), 'json') )
                else :
                    args['_json_arg'] = pd
                    argsrcs.update( {'_json_arg':'json'} )
                
            return ( self.ctrl_cgi, (w, args) )

        return ( self.ctrl_notfound, () )
    
    nonblock_postrecv = None
    
    def parse_multipart( self, wsgi_inpt, pdict, e ):
        
        if self.nonblock_postrecv :
            return self.nonblock_parse_multipart( wsgi_inpt, pdict, e )
    
        if type(pdict['boundary']) == str :
            pdict['boundary'] = pdict['boundary'].encode('ascii')
        r = cgi.parse_multipart(wsgi_inpt, pdict)

        rr = {}
        for k, v in r.items():
            if type(v[-1]) == str:
                rr[k] = v[-1].decode('utf-8')
            else:
                rr[k] = v[-1]
        return rr
        # return { k:v[-1].decode('utf-8') for k, v in r.items() }
        
    def nonblock_parse_multipart( self, wsgi_inpt, pdict, e ):
        
        #if type(pdict['boundary']) == str :
        #    pdict['boundary'] = pdict['boundary'].encode('ascii')
            
        #boundary = pdict['boundary']
        #boundary = boundary.encode('ascii') if type(boundary) == str else boundary
        #boundary = b'--'+boundary
        
        #blen = len(boundary)
        
        tmpfile = self.temp_postrecv()
        if tmpfile is None :
            raise Exception('must be use tmpfile.')
        
        with open( tmpfile, 'wb' ) as fp :
            
            while(True):
            
                data = wsgi_inpt.read(self.nonblock_postrecv)
                if len(data) == 0:
                    break
                
                fp.write(data)

        with open( tmpfile, 'rb' ) as fp :
            fs = cgi.FieldStorage(fp=fp, environ=e, keep_blank_values=1)
            r = dict([(self.parse_fieldstorage(k, fs[k])) for k in fs.keys() if not k.startswith('_') ])
            return r
    
    def parse_fieldstorage( self, k, v ):
        
        if str(type( v.file )) == "<class '_io.StringIO'>" :
            return (k, v.value)

        if str(type( v.file )) == "<class '_io.TextIOWrapper'>" :
            return (k, v.value)
        
        tmpfile = self.temp_postrecv()
        if tmpfile is None :
            raise Exception('must be use tmpfile.')
        
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        
        with open( tmpfile, 'wb' ) as fp :
            
            sz = 0
            while(True):
                
                d = v.file.read(self.nonblock_postrecv)
                
                sz += len(d)
                
                if len(d) == 0:
                    break
                
                md5.update(d)
                sha1.update(d)
                fp.write(d)
        
        return (k, {'filename':v.filename, 'stopath':tmpfile, 'filesize':sz, 'md5':md5.hexdigest(), 'sha1':sha1.hexdigest()} )

    
    def temp_postrecv( self ):
        return
    
    def http_cgi( self, work, args, argsrcs, cookie ):
        
        try :
            for k, p in work.__annotations__.items():
                if type(p) == type and k in args :
                    try :
                        if p == list:
                            if argsrcs[k] == 'qs' :
                                args[k] = json.loads(args[k]) if args[k].startswith('[') else args[k].split(',')
                            else :
                                assert type(args[k]) == p
                        elif p == bool:
                            if argsrcs[k] == 'qs' :
                                args[k] = {'true':True, 'false':False}[args[k].lower()]
                            else :
                                assert type(args[k]) == p
                        elif p == dict:
                            if argsrcs[k] == 'qs' :
                                args[k] = json.loads(args[k])
                                assert type(args[k]) == p
                            else :
                                assert type(args[k]) == p
                        elif p == datetime.datetime:
                            fmt = "%Y-%m-%dT%H:%M:%S" if 'T' in args[k] else "%Y-%m-%d %H:%M:%S"
                            args[k] = datetime.datetime.strptime(args[k], fmt)
                        elif p == datetime.date:
                            args[k] = datetime.datetime.strptime(args[k], "%Y-%m-%d").date()
                        elif p == datetime.time:
                            args[k] = datetime.datetime.strptime(args[k], "%H:%M:%S").time()
                        elif p == int :
                            if argsrcs[k] == 'qs' :
                                args[k] = int(args[k])
                            else :
                                assert type(args[k]) == p
                        elif p == float :
                            if argsrcs[k] == 'qs' :
                                args[k] = float(args[k])
                            else :
                                assert type(args[k]) == p
                        else :
                            args[k] = p(args[k])
                    except Exception as e:
                        print(e)
                        raise AssertionError('不符合条件的参数错误')
                    
            resp = work(**args)
        except Exception as e:
            return self.http_exception( e, args )

        if not isinstance( resp, HttpResponse ):
            resp = self.OK( [], resp )
            
        return resp
    
    def http_exception( self, e, args ):
        
        import traceback
        traceback.print_exc()
        
        if isinstance(e, TypeError) and e.args[0].startswith('url__') :
            return self.BadRequest([],'不符合要求的参数错误')
        
        if isinstance(e, AssertionError) :
            return self.BadRequest([],e.args[0])
        
        return self.InternalServerError( e )

    def http_notfound( self ):
        return self.NotFound()
    
    def ctrl_cgi( self, work, args ):
        
        try :
            resp = work(**args)
        except Exception as e:
            return self.ctrl_exception( e )

        if not isinstance( resp, HttpResponse ):
            resp = WsgiServer.OK( [], resp )
            
        return resp
    
    def ctrl_exception( self, e ):
        
        import traceback
        traceback.print_exc()
        
        return WsgiServer.InternalServerError( e )
    
    def ctrl_notfound( self ):
        return WsgiServer.NotFound()
    
    def uri( self, **kwargs ):
        
        a = self.env.args.copy()
        a.update( kwargs )
        
        params = urllib.parse.urlencode(a).strip()
        
        if params :
            return self.env.path+'?'+params
        
        return self.env.path
    
    def ws_entry( self, environ, wsresp ):
        
        path = environ['PATH_INFO']
        wi = 'ws'+path.replace('/','__')
        w = getattr( self, wi, None )
        
        if w == None :
            return self.ws_notfound, ()
        
        loop = asyncio.get_event_loop()
        if loop :
            return self.ws_async_cgi, (w, wsresp.wsc_args)
        
        return self.ws_notfound, (w,)
    
    def ws_notfound( self ):
        return
    
    def ws_cgi( self, work ):
        return
    
    def ws_async_cgi( self, work, ws_args ):
        
        try :
            
            import uwsgi
            import greenlet
            
            uwsgi.websocket_handshake()
            print("websockets...")
            
            me = greenlet.getcurrent()
            me.has_ws_msg = False
            me.task_ending = False
            me.sq_unregist = False
            me.rq_unregist = False
            
            self.ws = WSClient()
            for k, v in ws_args.items() :
                setattr(self.ws, k, v)
                
            self.t = asyncio.Task(self.ws_work(me, work))
            
            asyncio.get_event_loop().add_reader(uwsgi.connection_fd(), self.ws_recv_msg, me)
            
            f = asyncio.Future()
            asyncio.Task(self.ws_get_sq_msg(me, self.ws.sq, f))

            while not(me.task_ending and me.sq_unregist) :

                me.parent.switch()

                if f.done():
                    
                    r = f.result()
                    if r == Exception:
                        me.sq_unregist = True
                    else :
                        uwsgi.websocket_send(r)
                        f = asyncio.Future()
                        asyncio.Task(self.ws_get_sq_msg(me, self.ws.sq, f))
            
                if me.has_ws_msg:
                    
                    me.has_ws_msg = False
                    
                    try :
                        msg = uwsgi.websocket_recv_nb()
                    except OSError:
                        print('.......')
                        self.ws.sq.put(Exception)
                        asyncio.get_event_loop().remove_reader(uwsgi.connection_fd())
                        me.rq_unregist = True
                        self.t.cancel()
                        continue
                    
                    msg = msg.decode('utf-8')
                    self.ws.rq.put_nowait(msg)

            
            if me.rq_unregist == False :
                asyncio.get_event_loop().remove_reader(uwsgi.connection_fd())
                
            print('exit')
            
        except :
            import traceback
            traceback.print_exc()
            
        return
        
    @staticmethod
    async def ws_get_sq_msg(me, q, r):
        msg = await q.coro_get()
        r.set_result(msg)
        me.switch()
    
    @staticmethod
    def ws_recv_msg(me):
        me.has_ws_msg = True
        me.switch()
    
    @staticmethod
    async def ws_work(me, work):
        try :
            await work()
        except :
            import traceback
            traceback.print_exc()
        print('task ending')
        me.task_ending = True
        me.switch()
        return
    
    def srvcmd_ping( self, **kwargs ):
        return {'servertime':time.time()}
        
    def srvcmd_apidoc( self, **kwargs ):
        return list(self.generate_doc())
    
# code message meaning
# -32700 Parse error Invalid JSON was received by the server.
# An error occurred on the server while parsing the JSON text.
# -32600 Invalid Request The JSON sent is not a valid Request object.
# -32601 Method not found The method does not exist / is not available.
# -32602 Invalid params Invalid method parameter(s).
# -32603 Internal error Internal JSON-RPC error.
# -32000 to -32099 Server error Reserved for implementation-defined server-errors.

class JrOK(HttpOK):
    def __init__(self, headers=[], result=None):
        headers = headers + [('Content-Type','text/html; charset=utf-8')]
        super().__init__(headers, {'status':200, 'result':result} )
        return

class JrBadRequest(HttpBadRequest):
    def __init__(self, headers=[], reason='bad request'):
        headers = headers + [('Content-Type','text/html; charset=utf-8')]
        super().__init__(headers,{'status':400, 'error':reason} )
        return

class JrLockedResource(HttpLockedResource):
    def __init__(self, headers=[], reason='locked resource'):
        headers = headers + [('Content-Type','text/html; charset=utf-8')]
        super().__init__(headers,{'status':400, 'error':reason} )
        return

class JrNotFound(HttpNotFound):
    def __init__(self, headers=[], reason='not found'):
        headers = headers + [('Content-Type','text/html; charset=utf-8')]
        super().__init__(headers,{'status':404, 'error':reason} )
        return

class JrForbidden(HttpForbidden):
    def __init__(self, headers=[], reason='forbidden'):
        headers = headers + [('Content-Type','text/html; charset=utf-8')]
        super().__init__(headers, {'status':403, 'error':reason} )
        return

class JrInternalServerError(HttpInternalServerError):
    def __init__(self, exc_info=None, reason='internal error'):
        super().__init__(exc_info, {'status': 500, 'error':reason })
        return






class JrWsgiServer(WsgiServer):
    
    # Response = HttpResponse
    # Redirect = HttpRedirect
    # XRedirect = HttpXRedirect
    # File = HttpFile
    
    OK = JrOK
    BadRequest = JrBadRequest
    NotFound = JrNotFound
    Forbidden = JrForbidden
    InternalServerError = JrInternalServerError
    LockedResource = JrLockedResource
    
    
    
# 'REQUEST_METHOD': 'GET', 
# 'REQUEST_URI': '/repdb/subscribe', 
# 'PATH_INFO': '/repdb/subscribe', 
# 'QUERY_STRING': '', 
# 'SERVER_PROTOCOL': 'HTTP/1.1', 
# 'SCRIPT_NAME': '', 
# 'SERVER_NAME': 'localhost.localdomain', 
# 'SERVER_PORT': '9988', 
# 'REMOTE_ADDR': '10.110.1.231', 
# 'HTTP_HOST': '10.110.1.99:9988', 
# 'HTTP_CONNECTION': 'Upgrade', 
# 'HTTP_PRAGMA': 'no-cache', 
# 'HTTP_CACHE_CONTROL': 'no-cache', 
# 'HTTP_UPGRADE': 'websocket', 
# 'HTTP_ORIGIN': 'http://10.110.1.99:9988', 
# 'HTTP_SEC_WEBSOCKET_VERSION': '13', 
# 'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36', 
# 'HTTP_ACCEPT_ENCODING': 'gzip, deflate', 
# 'HTTP_ACCEPT_LANGUAGE': 'zh-CN,zh;q=0.9', 
# 'HTTP_SEC_WEBSOCKET_KEY': 'slt52XkZnToxlQNsbJw9nQ==', 
# 'HTTP_SEC_WEBSOCKET_EXTENSIONS': 'permessage-deflate; client_max_window_bits', 
# 'wsgi.input': <uwsgi._Input object at 0x7fe2065d0048>, 
# 'wsgi.file_wrapper': <built-in function uwsgi_sendfile>, 
# 'x-wsgiorg.fdevent.readable': <built-in function uwsgi_eventfd_read>, 
# 'x-wsgiorg.fdevent.writable': <built-in function uwsgi_eventfd_write>, 
# 'x-wsgiorg.fdevent.timeout': None, 
# 'wsgi.version': (1, 0), 
# 'wsgi.errors': <_io.TextIOWrapper name=2 mode='w' encoding='UTF-8'>, 
# 'wsgi.run_once': False, 
# 'wsgi.multithread': False, 
# 'wsgi.multiprocess': False, 
# 'wsgi.url_scheme': 'http', 
# 'uwsgi.version': b'2.0.17', 
# 'uwsgi.core': 19, 
# 'uwsgi.node': b'localhost.localdomain'







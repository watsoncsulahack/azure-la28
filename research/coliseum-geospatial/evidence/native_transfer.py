"""Resumable sequential native LAZ transfers; incomplete bytes never become sources."""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

USER_AGENT='IS699-Coliseum-Evidence/1.1'


def save(path,obj):
    path.write_text(json.dumps(obj,indent=2)+'\n')


def fetch_native(path,url,expected_bytes):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    receipt=path.with_suffix(path.suffix+'.receipt.json')
    partial=path.with_suffix(path.suffix+'.part')
    state=partial.with_suffix(partial.suffix+'.receipt.json')
    if path.exists():
        if path.stat().st_size!=expected_bytes:
            raise ValueError(f'Completed native cache has unexpected size: {path}')
        return path
    offset=partial.stat().st_size if partial.exists()else 0
    if offset>expected_bytes:
        raise ValueError('Partial download is larger than the catalog file')
    previous=json.loads(state.read_text())if state.exists()else {}
    if previous.get('url',url)!=url:
        raise ValueError('Partial download belongs to a different source URL')
    record={'url':url,'expected_bytes':expected_bytes,'initial_partial_bytes':offset,
            'started_utc':datetime.now(timezone.utc).isoformat(),
            'validator':previous.get('validator'),'status':'INCOMPLETE; not a downloaded source object'}
    validator=record['validator']
    try:
        if offset:
            length=min(offset,16384)
            record['phase']='prefix validation'
            with urlopen(Request(url,headers={'Range':f'bytes=0-{length-1}',
                         'User-Agent':USER_AGENT}),timeout=45)as response:
                content_range=response.headers.get('Content-Range','')
                if response.status!=206 or content_range!=f'bytes 0-{length-1}/{expected_bytes}':
                    raise ValueError(f'Server did not honor prefix range: {response.status} {content_range}')
                prefix=response.read(length)
                with partial.open('rb')as source:
                    if prefix!=source.read(length):
                        raise ValueError('Partial prefix differs from current source; retained for inspection')
                current=response.headers.get('ETag')or response.headers.get('Last-Modified')
                if validator and validator!=current:
                    raise ValueError('Source validator changed since previous partial transfer')
                validator=current
                record.update(validator=validator,prefix_verified=True)
        if offset<expected_bytes:
            headers={'User-Agent':USER_AGENT}
            if offset:
                headers['Range']=f'bytes={offset}-'
                if validator:headers['If-Range']=validator
            record['phase']='data transfer'
            save(state,record)
            with urlopen(Request(url,headers=headers),timeout=45)as response:
                record.update(http_status=response.status,etag=response.headers.get('ETag'),
                    last_modified=response.headers.get('Last-Modified'),http_date=response.headers.get('Date'),
                    content_range=response.headers.get('Content-Range'))
                if offset and (response.status!=206 or record['content_range']!=f'bytes {offset}-{expected_bytes-1}/{expected_bytes}'):
                    raise ValueError('Server did not honor exact resume range; partial bytes retained')
                if not offset and response.status!=200:
                    raise ValueError(f'Unexpected full-file status {response.status}')
                validator=record['etag']or record['last_modified']
                record['validator']=validator
                save(state,record)
                started=time.monotonic()
                with partial.open('ab'if offset else'wb')as output:
                    while chunk:=response.read(1024*1024):
                        output.write(chunk);output.flush()
                        print(json.dumps({'native_tile':path.name,'bytes':output.tell(),
                                          'total_bytes':expected_bytes}),flush=True)
                        if time.monotonic()-started>1800:
                            raise TimeoutError('Native body transfer exceeded 30 minutes; partial bytes retained')
        actual=partial.stat().st_size
        if actual!=expected_bytes:
            raise ValueError(f'Native transfer incomplete: {actual}/{expected_bytes} bytes')
        with partial.open('rb')as source:
            if source.read(4)!=b'LASF':raise ValueError('Transfer is not a LAS/LAZ file')
        partial.replace(path)
        record.update(status='COMPLETE_TRANSFER; native decoding/CRS checks required in acquire.py native',
                      retrieved_utc=datetime.now(timezone.utc).isoformat(),bytes=actual)
        save(receipt,record);state.unlink(missing_ok=True)
        print(json.dumps({'native_tile':path.name,'status':'COMPLETE','bytes':actual}),flush=True)
        return path
    except Exception as error:
        record.update(status='INCOMPLETE; bytes retained for resume',error=repr(error),
                      attempted_utc=datetime.now(timezone.utc).isoformat(),
                      partial_bytes=partial.stat().st_size if partial.exists()else 0,
                      validator=validator)
        if isinstance(error,HTTPError):
            body=partial.with_suffix(partial.suffix+'.http-error.txt')
            body.write_bytes(error.read(16384))
            record.update(http_status=error.code,retry_after=error.headers.get('Retry-After'),
                          http_date=error.headers.get('Date'),error_response_body=str(body),
                          error_response_etag=error.headers.get('ETag'))
        save(state,record)
        raise

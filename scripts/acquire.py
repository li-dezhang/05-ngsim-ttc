"""Acquire one original TXT member via bounded public HTTP byte ranges."""
from pathlib import Path
import hashlib,json,urllib.request,struct,zlib,datetime,shutil
from inspect_source import BASE,RemoteZip
ROOT=Path(__file__).resolve().parents[1]
URL=BASE+'/files/ae894ea3-70b5-400e-b8ed-dc60e1827224?download=true'
MEMBER='vehicle-trajectory-data/0750am-0805am/trajectories-0750am-0805am.txt'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    manifest=ROOT/'data/manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()).get('acquired_utc'):
        m=json.loads(manifest.read_text())
        if all((ROOT/f['path']).exists() for f in m['files']):
            for f in m['files']:assert sha(ROOT/f['path'])==f['sha256']
            print('All existing acquisition hashes verified');return
    assert shutil.disk_usage(raw).free>2_000_000_000
    files=[]
    for name,url,cap in [('portal_metadata.json',BASE+'.json',2_000_000),('US_101_Metadata_Documentation.pdf',BASE+'/files/50459f5f-c40b-4eec-b9a0-72dfef577f15?download=true',1_000_000)]:
        p=raw/name
        if not p.exists():
            with urllib.request.urlopen(url,timeout=60) as r:b=r.read(cap+1)
            assert len(b)<=cap;p.write_bytes(b)
        files.append({'path':str(p.relative_to(ROOT)),'url':url,'bytes':p.stat().st_size,'sha256':sha(p)})
    # Exact official nested stored ZIP: inspect_source.py records central directory.
    # Read local member header to verify name, method and CRC before downloading its body.
    remote=RemoteZip(URL,327638049);absolute_header=138128475+27031510
    remote.seek(absolute_header);header=remote.read(30);fields=struct.unpack('<4s5H3I2H',header)
    assert fields[0]==b'PK\x03\x04' and fields[3]==8
    name=remote.read(fields[-2]).decode();assert name==MEMBER
    remote.read(fields[-1]);start=remote.tell();size=32538014
    compressed=raw/'trajectories-0750am-0805am.deflate'
    if not compressed.exists():
        blob=remote.read(size);compressed.write_bytes(blob)
    else:blob=compressed.read_bytes()
    dec=zlib.decompressobj(-15);txt=dec.decompress(blob,167644917)
    assert len(txt)==167644916 and dec.eof and not dec.unconsumed_tail
    assert zlib.crc32(txt)==3937205269
    path=raw/'trajectories-0750am-0805am.txt'
    if path.exists():assert path.read_bytes()==txt
    else:path.write_bytes(txt)
    for p in [compressed,path]:
        files.append({'path':str(p.relative_to(ROOT)),'url':URL,'range':f'bytes={start}-{start+size-1}','nested_member':'us-101-vehicle-trajectory-data.zip/'+MEMBER,'bytes':p.stat().st_size,'sha256':sha(p),'crc32_uncompressed':3937205269})
    m={'acquired_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_page':'https://data.transportation.gov/d/8ect-6jqj','official_metadata_edition':'Version 1, publication 2016, metadata 20160408; observations June 15 2005','portal_rows_updated_at':json.loads((raw/'portal_metadata.json').read_text())['rowsUpdatedAt'],'scope':'original TXT of official named 0750am-0805am member only','archive_size_not_downloaded':327638049,'trajectory_compressed_transfer_bytes':size,'licence':'Portal CC BY-SA 3.0; legacy RDE metadata requires attribution and asks users to refrain from raw redistribution; keep raw local and flag release distinction','files':files}
    if manifest.exists() and json.loads(manifest.read_text()).get('acquired_utc'):
        old=json.loads(manifest.read_text())
        for f in files:
            prior=next(x for x in old['files'] if x['path']==f['path'])
            assert f['sha256']==prior['sha256'],'Source version changed'
    else:manifest.write_text(json.dumps(m,indent=2)+'\n')
    for f in files:(ROOT/f['path']).chmod(0o444)
    print(json.dumps(m,indent=2))
if __name__=='__main__':main()

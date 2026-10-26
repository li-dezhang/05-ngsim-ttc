"""Bounded official metadata and ZIP-directory inspection; no trajectory extraction."""
from pathlib import Path
import io,json,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
BASE='https://data.transportation.gov/api/views/8ect-6jqj'
class RemoteZip(io.RawIOBase):
    def __init__(self,url,size):self.url=url;self.size=size;self.pos=0;self.transferred=0
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,n,whence=0):
        self.pos=n if whence==0 else self.pos+n if whence==1 else self.size+n
        return self.pos
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        n=min(n,self.size-self.pos)
        if n==0:return b''
        if n>50_000_000:raise ValueError('Single member read exceeds bounded 50 MB')
        req=urllib.request.Request(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'})
        with urllib.request.urlopen(req,timeout=60) as r:
            if r.status!=206:raise ValueError(f'Server did not honor Range: {r.status}')
            data=r.read(n+1)
        if len(data)!=n:raise ValueError('Incomplete range')
        self.pos+=len(data);self.transferred+=len(data)
        return data
def main():
    raw=ROOT/'data/raw';raw.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(BASE+'.json',timeout=40) as r:data=r.read(2_000_000)
    target=raw/'portal_metadata.json'
    if target.exists():assert target.read_bytes()==data, 'Existing metadata differs; preserve it'
    else:target.write_bytes(data)
    u=BASE+'/files/50459f5f-c40b-4eec-b9a0-72dfef577f15?download=true'
    with urllib.request.urlopen(u,timeout=40) as r:
        pdf=r.read(1_000_001)
        assert len(pdf)==557844 and pdf[:4]==b'%PDF'
    target=raw/'US_101_Metadata_Documentation.pdf'
    if target.exists():assert target.read_bytes()==pdf, 'Existing dictionary differs; preserve it'
    else:target.write_bytes(pdf)
    remote=RemoteZip(BASE+'/files/ae894ea3-70b5-400e-b8ed-dc60e1827224?download=true',327638049)
    with zipfile.ZipFile(remote) as z:
        rows=[{'name':x.filename,'bytes':x.file_size,'compressed_bytes':x.compress_size,'crc32':x.CRC,'compression':x.compress_type} for x in z.infolist()]
    (ROOT/'data/interim/official_zip_directory.json').write_text(json.dumps(rows,indent=2)+'\n')
    print('Directory entries',len(rows),'transferred',remote.transferred)
    for row in rows:
        if any(s in row['name'].lower() for s in ['traject','metadata','dictionary']):print(row)
if __name__=='__main__':main()

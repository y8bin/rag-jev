"""Resume frozen answers with token-window pacing after an HTTP 429.

Only request timing changes. Keep all existing successes, raw responses, cached
choices, uncertain budget reservations, prompts and provider settings.
"""
import asyncio
from collections import deque
import time
from pathlib import Path
import tiktoken
import run_koblex_reproduction_answers as runner
from legal_rag_jev.providers import Transport
from legal_rag_jev.io import read_json,write_json,file_hash

class TokenWindow:
    def __init__(self,limit=350000,period=60):
        self.limit,self.period=limit,period
        self.events=deque();self.lock=asyncio.Lock()

    async def acquire(self,weight):
        if weight>self.limit:raise ValueError('One request exceeds pacing token window')
        async with self.lock:
            while True:
                now=time.monotonic()
                while self.events and self.events[0][0]<=now-self.period:self.events.popleft()
                if sum(w for _,w in self.events)+weight<=self.limit:
                    self.events.append((now,weight));return
                await asyncio.sleep(max(.01,self.events[0][0]+self.period-now+.1))

class PacedTransport(Transport):
    def __init__(self,cfg):
        super().__init__(cfg)
        self.window=TokenWindow()
        self.encoding=tiktoken.encoding_for_model('gpt-4o-2024-08-06')

    async def request(self,kind,identity,path,body=None):
        if body is not None:
            text='\n'.join(m.get('content','') for m in body.get('messages',[]))
            tokens=len(self.encoding.encode(text,disallowed_special=()))+body.get('max_tokens',0)+256
            await self.window.acquire(tokens)
        return await super().request(kind,identity,path,body)

async def main():
    path=runner.study.ROOT/'rate-limit-amendment.json'
    amendment={'reason':'Observed provider HTTP429 TPM450000; previous runner stopped and preserved all completed rows.',
               'pacing_tokens_per_60_seconds':350000,'tokenizer':'o200k_base; prompt + maximum output +256 framing',
               'scientific_parameters_changed':False,'cached_successes_preserved':True,
               'budget_reservations_retained':True,'runner_sha256':file_hash(__file__),
               'parent_answer_runner_sha256':file_hash(runner.__file__)}
    if path.exists() and read_json(path)!=amendment:raise ValueError('Pacing amendment changed')
    write_json(path,amendment)
    runner.Transport=PacedTransport
    await runner.main()

if __name__=='__main__':asyncio.run(main())

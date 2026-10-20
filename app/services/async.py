import asyncio

semaphore=asyncio.Semaphore(5)

async def process_pdf(pdf):
    async with semaphore:
        return await extract(pdf)
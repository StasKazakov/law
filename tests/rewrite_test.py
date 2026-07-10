import asyncio
from rewrite.functions import rephrase_question

async def main():
    query = "Підстави для продовження строків апеляційного розгляду адміністративної справи в умовах воєнного стану"
    
    answer = await rephrase_question(query) 
    
    print(answer)

if __name__ == "__main__":
    asyncio.run(main())
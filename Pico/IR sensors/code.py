import serial_asyncio
import asyncio

async def main():

    ser_reader, ser_writer = await serial_asyncio.open_serial_connection(url='/dev/ttyACM1')

    print(ser_reader, ser_writer)
    
if __name__ == '__main__':

    asyncio.run(main())


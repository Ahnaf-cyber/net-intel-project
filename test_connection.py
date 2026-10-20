from clickhouse_driver import Client

client = Client(host='localhost', user='default', password='')

result = client.execute('SELECT count(*) FROM domains')
print("Total domains in database:", result)

sample = client.execute('SELECT * FROM domains LIMIT 5')
print("First 5 rows:")
for row in sample:
    print(row)

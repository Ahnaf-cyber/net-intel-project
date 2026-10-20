from clickhouse_driver import Client
import csv

client = Client(host='localhost', user='default', password='')

# আগে পুরনো ডেটা মুছে ফেলি, যাতে বারবার চালালে ডুপ্লিকেট না হয়
client.execute('TRUNCATE TABLE domains')
print("Old data cleared.")

# CSV ফাইল পড়ি এবং সব সারি একটা লিস্টে জমা করি
rows = []
with open('top-1m.csv', 'r') as f:
    reader = csv.reader(f)
    for line in reader:
        rank = int(line[0])
        domain = line[1]
        rows.append((rank, domain))

print(f"Read {len(rows)} rows from CSV.")

# একসাথে সব ডেটা ডাটাবেসে ঢুকাই (batch insert, এটা দ্রুত)
client.execute('INSERT INTO domains (rank, domain) VALUES', rows)
print("Data inserted successfully.")

# যাচাই করি
result = client.execute('SELECT count(*) FROM domains')
print("Total rows in table now:", result[0][0])

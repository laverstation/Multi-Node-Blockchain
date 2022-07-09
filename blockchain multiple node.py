import sys
import hashlib
import json

from time import time
from uuid import uuid4

from flask import Flask
from flask.globals import request
from flask.json import jsonify

import requests
from urllib.parse import urlparse


# Kamus Crypto
# Hash = Sebuah kata yang sudah di translate ke dalam SHA sehingga hasilnya acak
# Block = Tempat menyimpan berbagai transaksi yang terjadi dalam kurun waktu tertentu dan target tertentu
# Node = Komputer Komputer yang menambang kripto atau menjalankan transaksi di kripto atau yang memecahkan hash yang punya data block
# Chain = Rantai yang menghubungkan block 1 dengan block lainnya
# POW = Proses memecahkan hashing sebelumnya dan menambah nonce kemudian menguploadnya kembali ke block selanjutnya
# Nonce = Nomer yang dipakai hanya sekali, nomer ini untuk menambahkan kesulitan untuk memcahkan hash berikutnya sehingga si penambang mendapatkan reward dari memecahkan hash sebelumnya yang sudah diberikan nonce
# Index = Urutan Block
# Content = Hash yang diacak
# Transaction = Sebuah Kegiatan Apapun yang dicatat di sistem


class Blockchain(object):
    # Target kesusahan yang ingin dicapai makin banyak makin baik(sulit)
    difficulty_target = "0000"

    # Fungsi Melakukan Hashing Block
    def hash_block(self, block):
        # Buat code block dan diurutkan secara key/ascending descending json.dumps convert python objek ke json
        block_encoded = json.dumps(block, sort_keys=True).encode()
        # Melakukan hashing dan kembalikan encoded data ke dalam heximal format
        return hashlib.sha256(block_encoded).hexdigest()

    # Fungsi Membuat Block Baru
    def __init__(self):
        # Wadah untuk saling menambahkan node (set = saling menambahkan)
        self.nodes = set()

        # Wadah data chain
        self.chain = []

        # Wadah data sementara
        self.current_transaction = []

        # Menciptakan block dan hash pertama
        genesis_hash = self.hash_block("genesis_block")

        # Menambahkan block
        self.append_block(
            # Mencari hash previos dari genesis hash
            hash_of_previous_block=genesis_hash,
            # Mencari nonce yang akan digunakan untuk menambah kesulitan
            nonce=self.proof_of_work(0, genesis_hash, [])
        )

    # Fungsi untuk menambahkan node
    def add_node(self, address):
        # Menguraikan Url (address) dengan library urlparse
        parse_url = urlparse(address)
        # Menambahkan wadah node dengan url yang sudah diurai di netloc
        self.nodes.add(parse_url.netloc)
        print(parse_url.netloc)

    # Fungsi untuk memeriksa validasi chain dan memverifikasi nonce
    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        # Melakukan looping jika index saat ini kurang dari panjang chain
        while current_index < len(chain):
            # Menampung data block dengan isi chain dari index saat ini
            block = chain[current_index]

            # Cek hash sebelumnya apakah sama dengan hash dari block terakhir
            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False

            # Cek apakah nonce, hash, dan transaction dari block sebelumnya sama tidak
            if not self.valid_proof(
                    current_index,
                    block['hash_of_previous_block'],
                    block['transaction'],
                    block['nonce']):
                return False

            # Jika semuanya sudah sama maka block terakhir menjadi block saat ini dan nilai index bertamabh
            last_block = block
            current_index += 1

        return True

    # Fungsi Update atau Sinkronisasi Blockchain
    def update_blockchain(self):
        # Mencari node terdekat
        neighbours = self.nodes
        # Asumsi chainnya belum ada nilai jika sudah ada nilai maka akan mencari chain yang paling panjang
        new_chain = None

        # Mencari chain terpanjang
        max_length = len(self.chain)

        # Melakukan verifikasi semua node dengan Looping
        for node in neighbours:
            # Memanggil isi Blockchain
            response = requests.get(f'http://{node}/blockchain')

            # Jika Datanya benar dan ditemukan
            if response.status_code == 200:
                # Tampung data response dari panjang index dan chain
                length = response.json()['length']
                chain = response.json()['chain']

                # Memeriksa apakah panjangnya valid dan lebih panjang dari max_length
                if length > max_length and self.valid_chain(chain):
                    # Jika Benar maka max lenghtnya diubah ke length dan new chain diuabh ke chain
                    max_length = length
                    new_chain = chain

                # Mengganti rantai saat ini dengan node yang memiliki rantai terpanjang
                if new_chain:
                    self.chain = new_chain
                    return True

        return False

    # Fungsi Menyelesaikan Hash dan Membuat Nonce
    def proof_of_work(self, index, hash_of_previous_block, transactions):
        nonce = 0
        # Buat Looping sampai nonce nya sesuai target
        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1
        return nonce

    # Fungsi Untuk Memvalidasi Hash
    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        # Menampung konten dalam bentuk string dan di encode
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()
        # Hashing konten kedalam hex format
        content_hash = hashlib.sha256(content).hexdigest()
        # Nilai hash yang muncul apakah sama dengan target yang diinginkan jika sama maka berhenti mencari
        return content_hash[:len(self.difficulty_target)] == self.difficulty_target

    # Fungsi Menambahkan Block Baru
    def append_block(self, nonce, hash_of_previous_block):
        block = {
            # Index adalah Panjang dari Block
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transaction,
            # Nonce adalah angka sekali pakai yang berguna untuk menambah kesulitan pada hash
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        # Reset transaksi yang sudah selesai karena akan digantikan oleh yang baru
        self.current_transaction = []

        # Menampilkan Block baru yang sudah dibuat
        self.chain.append(block)
        return block

    # Fungsi untuk membuat transaksi
    def add_transaction(self, sender, recipient, amount):
        # Mengisi data transaksi dengan parameter diatas
        self.current_transaction.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender
        })
        # Kembalikan nilai transaksinya ke Block terakhir
        return self.last_block['index'] + 1

    # Memasukan Nilai Block terakhir kedalam Chain
    @property
    def last_block(self):
        return self.chain[-1]


# Memanggil API
app = Flask(__name__)
# Membuat Address Penambang
node_identifier = str(uuid4()).replace('-', "")
# Meringkas Class supaya bisa di panggil
blockchain = Blockchain()


# Routes / End Point / URL Blockhain
@app.route('/blockchain', methods=['GET'])
# Semua data di blockchain ditampilkan
def full_chain():
    response = {
        'chain': blockchain.chain,
        'lenght': len(blockchain.chain)
    }
    # Mengembalikan objek respon pada aplikasi
    return jsonify(response), 200


# Route Menambang == Menambahkan Data (Nounce)
@app.route('/mine', methods=['GET'])
# Fungsi Reward Penambang
def mine_block():
    # Menambahkan transaksi penambang
    blockchain.add_transaction(
        # Pengirim (0 = Diberi oleh jaringan blockchain)
        sender="0",
        recipient=node_identifier,
        # Rewardnya
        amount=1
    )

    # Mencari Hash dari Block Sebelumnya
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    # Memanggil POW untuk menemukan nounce
    index = len(blockchain.chain)
    # Mencari Nounce dari proof of work
    nonce = blockchain.proof_of_work(
        index, last_block_hash, blockchain.current_transaction)
    # Block Berhasil ditambahkan setelah nounce sudah ketemu dengan proses POW
    block = blockchain.append_block(nonce, last_block_hash)
    # Pemberitahuan Block Telah Berhasil Ditambahkan
    response = {
        'message': "Block baru telah ditambahkan (Mined)",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction']
    }
    # Menampilkan respon aplikasi
    return jsonify(response), 200


# Route Menambahkan Transaksi Baru
@app.route('/transaction/new', methods=['POST'])
# Fungsi Menambahkan transaksi
def new_transaction():
    # Value(dan data) semua client yang diinput diambil dengan json
    values = request.get_json()
    # Input Membutuhkan Parameter berikut
    required_fields = ['sender', 'recipient', 'amount']

    # Jika Status validasi ada yang kosong
    if not all(k in values for k in required_fields):
        return ('Missing Fields', 400)

    # Jika Status Validasi Benar
    index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )

    # Pemberitahuan Penambahan Transaksi
    response = {'message': f'Transaksi Akan Ditambahkan Ke Blok'}
    # Menampilkan Respon Aplikasi
    return(jsonify(response), 201)


# Route Menambahkan Node
@app.route('/nodes/add_nodes', methods=['POST'])
# Fungsi menambahkan nodes
def add_nodes():
    # Mendapatkan node yang didapatkan dari client
    values = request.get_json()
    # Data json yang didapat akan ditampung di 'nodes'
    nodes = values.get('nodes')

    # Jika setelah saling menambahkan nodenya kosong atau tidak diisi maka akan error
    if nodes is None:
        return "ERROR, Missing Node(s) Info", 400

    # Jika ternyata data nodenya terisi maka akan di looping dan ditambahkan ke node dalam blockchain
    for node in nodes:
        blockchain.add_node(node)

    # Respon dari add node
    response = {
        'message': 'Node baru telah ditambahkan',
        'nodes': list(blockchain.nodes)
    }
    # Memanggil dengan response
    return jsonify(response), 200


# Route Sinkronisasi Update Chain antar node
@app.route('/nodes/sync', methods=['GET'])
# Fungsi sinkronisasi
def sync():
    # Variabel update menampung update dari blockchain
    updated = blockchain.update_blockchain()
    # Respon dari data blockchain jika baru di update
    if updated:
        response = {
            'message': 'Blockchain telah diupdate dengan data terbaru',
            'blockchain': blockchain.chain
        }
    # Respon dari data blockchain jika data sudah di update
    else:
        response = {
            'message': 'Blockchain sudah menggunakan data paling terbaru',
            'blockchain': blockchain.chain
        }

    return jsonify(response), 200


# Jalankan Server Flask
if __name__ == '__main__':
    # Jika Name = Jalan maka jalankan dengan host dan port
    app.run(host='0.0.0.0', port=int(sys.argv[1]))

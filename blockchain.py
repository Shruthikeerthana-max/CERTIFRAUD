import hashlib
import json
from time import time
import os
from typing import Dict, List, Optional

class Blockchain:
    def __init__(self):
        self.chain: List[Dict] = []
        self.current_transactions: List[Dict] = []
        self.certificates: Dict[str, Dict] = {}  # Track certificates by hash
        
        # Initialize with genesis block
        self.new_block(previous_hash="1", proof=100)
        
        # Load existing data if available
        self.load_chain()

    def new_block(self, proof: int, previous_hash: Optional[str] = None) -> Dict:
        """
        Create a new Block in the Blockchain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        # Add certificates to registry
        for tx in block['transactions']:
            if 'certificate_hash' in tx:
                self.certificates[tx['certificate_hash']] = {
                    'block_index': block['index'],
                    'student': tx['student'],
                    'issuer': tx['issuer'],
                    'timestamp': block['timestamp']
                }

        self.chain.append(block)
        self.save_chain()
        return block

    def new_certificate(self, issuer: str, student: str, certificate_data: Dict) -> str:
        """
        Creates a new certificate and returns its hash
        """
        certificate_hash = self.hash(certificate_data)
        self.new_transaction(
            issuer=issuer,
            student=student,
            certificate_hash=certificate_hash
        )
        return certificate_hash

    def new_transaction(self, issuer: str, student: str, certificate_hash: str) -> int:
        """
        Adds a new transaction to the list of transactions
        """
        self.current_transactions.append({
            'issuer': issuer,
            'student': student,
            'certificate_hash': certificate_hash,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(data) -> str:
        """
        Creates a SHA-256 hash of any data
        """
        if isinstance(data, dict):
            # Convert dictionary to string first
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def last_block(self) -> Dict:
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes
        - p is the previous proof, p' is the new proof
        """
        proof = 0
        while not self.valid_proof(last_proof, proof):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """
        Validates the Proof
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def verify_certificate(self, certificate_hash: str) -> Dict:
        """
        Verify if a certificate exists in the blockchain
        Returns:
            {
                "status": "VALID" | "INVALID",
                "block_index": int,
                "timestamp": float,
                "student": str,
                "issuer": str
            }
        """
        if certificate_hash in self.certificates:
            return {
                "status": "VALID",
                **self.certificates[certificate_hash]
            }
        return {"status": "INVALID"}

    def save_chain(self):
        """Save blockchain to disk"""
        with open('blockchain_data.json', 'w') as f:
            json.dump({
                'chain': self.chain,
                'certificates': self.certificates
            }, f)

    def load_chain(self):
        """Load blockchain from disk if exists"""
        if os.path.exists('blockchain_data.json'):
            with open('blockchain_data.json', 'r') as f:
                data = json.load(f)
                self.chain = data.get('chain', [])
                self.certificates = data.get('certificates', {})
                
                # Rebuild current transactions from last block
                if self.chain:
                    self.current_transactions = self.chain[-1].get('transactions', [])

    def validate_chain(self) -> bool:
        """
        Validate the integrity of the blockchain
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            # Check hash integrity
            if current_block['previous_hash'] != self.hash(previous_block):
                return False

            # Check proof of work
            if not self.valid_proof(previous_block['proof'], current_block['proof']):
                return False

        return True
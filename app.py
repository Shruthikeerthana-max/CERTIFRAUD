from flask import Flask, jsonify, request
from flask_cors import CORS
from blockchain import Blockchain
import json
from typing import Dict, Any

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
blockchain = Blockchain()

@app.route('/api/issue', methods=['POST'])
def issue_certificate() -> Dict[str, Any]:
    """
    Issue a new certificate and add to blockchain
    Expected JSON:
    {
        "issuer": "Institution Name",
        "student": "Student Name",
        "certificate_data": {
            "degree": "B.Tech IT",
            "year": 2024,
            ...
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        required = ['issuer', 'student', 'certificate_data']
        if not all(k in data for k in required):
            return jsonify({'error': f'Missing fields. Required: {required}'}), 400

        if not isinstance(data['certificate_data'], dict):
            return jsonify({'error': 'certificate_data must be a JSON object'}), 400

        cert_hash = blockchain.hash(data['certificate_data'])
        index = blockchain.new_transaction(
            issuer=data['issuer'],
            student=data['student'],
            certificate_hash=cert_hash
        )

        last_block = blockchain.last_block
        proof = blockchain.proof_of_work(last_block['proof'])
        block = blockchain.new_block(proof)

        return jsonify({
            'message': 'Certificate issued successfully',
            'block_index': block['index'],
            'certificate_hash': cert_hash,
            'timestamp': block['timestamp'],
            'transaction_index': index
        }), 201

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/verify', methods=['POST', 'OPTIONS'])
def verify_certificate() -> Dict[str, Any]:
    """
    Verify certificate existence
    Accepts:
    - POST with JSON: {"certificate_data": {...}} or {"certificate_hash": "..."}
    """
    try:
        if request.method == 'OPTIONS':
            return jsonify({}), 200

        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        if 'certificate_hash' in data:
            cert_hash = data['certificate_hash']
        elif 'certificate_data' in data:
            cert_hash = blockchain.hash(data['certificate_data'])
        else:
            return jsonify({'error': 'Provide either certificate_hash or certificate_data'}), 400

        verification = blockchain.verify_certificate(cert_hash)
        
        if verification['status'] == 'VALID':
            return jsonify({
                'valid': True,
                'certificate_hash': cert_hash,
                'block_index': verification['block_index'],
                'timestamp': verification['timestamp'],
                'issuer': verification['issuer'],
                'student': verification['student']
            }), 200
        else:
            return jsonify({
                'valid': False,
                'certificate_hash': cert_hash,
                'message': 'Certificate not found in blockchain'
            }), 404

    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500

@app.route('/api/verify/<string:certificate_hash>', methods=['GET'])
def verify_certificate_by_hash(certificate_hash: str) -> Dict[str, Any]:
    """
    Verify certificate by hash (GET endpoint)
    """
    try:
        verification = blockchain.verify_certificate(certificate_hash)
        
        if verification['status'] == 'VALID':
            return jsonify({
                'valid': True,
                'certificate_hash': certificate_hash,
                'block_index': verification['block_index'],
                'timestamp': verification['timestamp'],
                'issuer': verification['issuer'],
                'student': verification['student']
            }), 200
        else:
            return jsonify({
                'valid': False,
                'certificate_hash': certificate_hash,
                'message': 'Certificate not found in blockchain'
            }), 404

    except Exception as e:
        return jsonify({'error': f'Verification failed: {str(e)}'}), 500

@app.route('/api/chain', methods=['GET'])
def get_chain() -> Dict[str, Any]:
    """Return the full blockchain"""
    return jsonify({
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
        'valid': blockchain.validate_chain()
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'chain_valid': blockchain.validate_chain(),
        'blocks': len(blockchain.chain),
        'pending_transactions': len(blockchain.current_transactions)
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
Lightweight Private Blockchain for Traffic Signal Management
============================================================
This module implements a lightweight private blockchain to ensure secure and 
reliable communication for traffic signal management. Each traffic signal state 
change is recorded as an immutable transaction in the blockchain, providing:
- Data Integrity: Cryptographic hashing ensures tamper-proof records
- Consensus: Multiple nodes can validate and agree on signal states
- Transparency: Complete audit trail of all signal changes
- Security: Private blockchain with controlled node access
"""

import hashlib
import json
import time
from typing import List, Dict, Optional, Any
from datetime import datetime


class Transaction:
    """Represents a single traffic signal state change transaction"""
    
    def __init__(self, lane_id: int, signal_state: str, vehicle_count: int, 
                 green_time: int, emergency_vehicle: bool = False, 
                 node_id: str = "main", metadata: Optional[Dict] = None):
        """
        Initialize a traffic signal transaction
        
        Args:
            lane_id: ID of the lane/intersection
            signal_state: Current signal state ('GREEN', 'RED', 'YELLOW')
            vehicle_count: Number of vehicles detected
            green_time: Calculated green light duration in seconds
            emergency_vehicle: Whether emergency vehicle is present
            node_id: ID of the node making the change
            metadata: Additional transaction metadata
        """
        self.lane_id = lane_id
        self.signal_state = signal_state
        self.vehicle_count = vehicle_count
        self.green_time = green_time
        self.emergency_vehicle = emergency_vehicle
        self.node_id = node_id
        self.timestamp = datetime.utcnow().isoformat()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary for hashing and storage"""
        return {
            'lane_id': self.lane_id,
            'signal_state': self.signal_state,
            'vehicle_count': self.vehicle_count,
            'green_time': self.green_time,
            'emergency_vehicle': self.emergency_vehicle,
            'node_id': self.node_id,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    def __repr__(self):
        return f"Transaction(lane={self.lane_id}, state={self.signal_state}, vehicles={self.vehicle_count})"


class Block:
    """Represents a single block in the blockchain"""
    
    def __init__(self, index: int, transactions: List[Transaction], 
                 previous_hash: str, nonce: int = 0):
        """
        Initialize a blockchain block
        
        Args:
            index: Block index/height in the chain
            transactions: List of transactions in this block
            previous_hash: Hash of the previous block
            nonce: Proof-of-work nonce (for mining)
        """
        self.index = index
        self.timestamp = datetime.utcnow().isoformat()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate the cryptographic hash of this block"""
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int = 2):
        """
        Mine the block using proof-of-work algorithm
        
        Args:
            difficulty: Number of leading zeros required in hash
        """
        target = "0" * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary for serialization"""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }
    
    def __repr__(self):
        return f"Block(index={self.index}, hash={self.hash[:16]}..., tx_count={len(self.transactions)})"


class Blockchain:
    """Lightweight private blockchain for traffic signal management"""
    
    def __init__(self, node_id: str = "main", difficulty: int = 2, 
                 block_size: int = 5):
        """
        Initialize the blockchain
        
        Args:
            node_id: Unique identifier for this blockchain node
            difficulty: Mining difficulty (number of leading zeros)
            block_size: Maximum transactions per block
        """
        self.chain: List[Block] = [self.create_genesis_block()]
        self.pending_transactions: List[Transaction] = []
        self.node_id = node_id
        self.difficulty = difficulty
        self.block_size = block_size
        self.known_nodes: set = {node_id}  # Track known blockchain nodes
    
    def create_genesis_block(self) -> Block:
        """Create the first (genesis) block in the blockchain"""
        genesis_tx = Transaction(
            lane_id=0,
            signal_state='INIT',
            vehicle_count=0,
            green_time=0,
            node_id='genesis',
            metadata={'message': 'Genesis block for Traffic Signal Blockchain'}
        )
        return Block(0, [genesis_tx], "0" * 64)  # Previous hash is all zeros
    
    def get_latest_block(self) -> Block:
        """Get the most recent block in the chain"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the pending transactions pool
        
        Args:
            transaction: Transaction to add
            
        Returns:
            True if transaction was added, False otherwise
        """
        # Validate transaction before adding
        if not self.validate_transaction(transaction):
            return False
        
        self.pending_transactions.append(transaction)
        
        # Automatically mine block if we reach block size
        if len(self.pending_transactions) >= self.block_size:
            self.mine_pending_transactions()
        
        return True
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate a transaction before adding to pool
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation checks
        if transaction.lane_id < 0:
            return False
        if transaction.signal_state not in ['GREEN', 'RED', 'YELLOW', 'INIT']:
            return False
        if transaction.vehicle_count < 0:
            return False
        if transaction.green_time < 0:
            return False
        
        return True
    
    def mine_pending_transactions(self, mining_reward_node: Optional[str] = None) -> Block:
        """
        Mine all pending transactions into a new block
        
        Args:
            mining_reward_node: Node ID that will receive mining reward (optional)
            
        Returns:
            The newly mined block
        """
        if not self.pending_transactions:
            return None
        
        # Create reward transaction if specified
        if mining_reward_node:
            reward_tx = Transaction(
                lane_id=0,
                signal_state='REWARD',
                vehicle_count=0,
                green_time=0,
                node_id=mining_reward_node,
                metadata={'type': 'mining_reward'}
            )
            self.pending_transactions.append(reward_tx)
        
        # Get transactions up to block size
        transactions_to_mine = self.pending_transactions[:self.block_size]
        self.pending_transactions = self.pending_transactions[self.block_size:]
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            transactions=transactions_to_mine,
            previous_hash=self.get_latest_block().hash
        )
        
        # Mine the block (proof-of-work)
        new_block.mine_block(self.difficulty)
        
        # Add to chain
        self.chain.append(new_block)
        
        return new_block
    
    def is_chain_valid(self) -> bool:
        """
        Validate the entire blockchain integrity
        
        Returns:
            True if chain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if block points to previous block correctly
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_transactions_by_lane(self, lane_id: int) -> List[Transaction]:
        """
        Get all transactions for a specific lane
        
        Args:
            lane_id: Lane ID to query
            
        Returns:
            List of transactions for the lane
        """
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.lane_id == lane_id:
                    transactions.append(tx)
        return transactions
    
    def get_latest_signal_state(self, lane_id: int) -> Optional[Transaction]:
        """
        Get the latest signal state for a specific lane
        
        Args:
            lane_id: Lane ID to query
            
        Returns:
            Latest transaction for the lane, or None if not found
        """
        # Search from most recent to oldest
        for block in reversed(self.chain):
            for tx in reversed(block.transactions):
                if tx.lane_id == lane_id and tx.signal_state in ['GREEN', 'RED', 'YELLOW']:
                    return tx
        return None
    
    def add_node(self, node_id: str):
        """Add a known node to the network"""
        self.known_nodes.add(node_id)
    
    def replace_chain(self, new_chain: List[Block]) -> bool:
        """
        Replace current chain with a new chain if it's longer and valid
        
        Args:
            new_chain: New blockchain to replace current one
            
        Returns:
            True if chain was replaced, False otherwise
        """
        if len(new_chain) <= len(self.chain):
            return False
        
        # Validate the new chain
        temp_chain = Blockchain(self.node_id, self.difficulty, self.block_size)
        temp_chain.chain = new_chain
        
        if not temp_chain.is_chain_valid():
            return False
        
        # Replace current chain
        self.chain = new_chain
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert blockchain to dictionary for serialization"""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'node_id': self.node_id,
            'difficulty': self.difficulty,
            'block_size': self.block_size,
            'known_nodes': list(self.known_nodes)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        lane_transactions = {}
        
        for block in self.chain:
            for tx in block.transactions:
                if tx.lane_id not in lane_transactions:
                    lane_transactions[tx.lane_id] = 0
                lane_transactions[tx.lane_id] += 1
        
        return {
            'total_blocks': len(self.chain),
            'total_transactions': total_transactions,
            'pending_transactions': len(self.pending_transactions),
            'lane_transactions': lane_transactions,
            'is_valid': self.is_chain_valid(),
            'node_id': self.node_id,
            'known_nodes': len(self.known_nodes)
        }
    
    def __repr__(self):
        return f"Blockchain(node={self.node_id}, blocks={len(self.chain)}, pending={len(self.pending_transactions)})"


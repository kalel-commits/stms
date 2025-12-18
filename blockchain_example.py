"""
Blockchain Example for Traffic Signal Management
================================================
This example demonstrates how the blockchain records traffic signal changes.
Run this script to see the blockchain in action.
"""

from blockchain import Blockchain, Transaction
import time

def main():
    print("=" * 60)
    print("Blockchain Example: Traffic Signal Management")
    print("=" * 60)
    print()
    
    # Initialize blockchain
    print("1. Initializing blockchain...")
    blockchain = Blockchain(
        node_id="example_node",
        difficulty=2,
        block_size=3  # Smaller block size for demo
    )
    print(f"   ✓ Blockchain created: {blockchain.node_id}")
    print(f"   ✓ Genesis block created: {blockchain.get_latest_block().hash[:16]}...")
    print()
    
    # Create some sample transactions
    print("2. Creating traffic signal transactions...")
    transactions = [
        Transaction(
            lane_id=1,
            signal_state="GREEN",
            vehicle_count=15,
            green_time=52,
            emergency_vehicle=False,
            node_id="example_node"
        ),
        Transaction(
            lane_id=2,
            signal_state="RED",
            vehicle_count=8,
            green_time=42,
            emergency_vehicle=False,
            node_id="example_node"
        ),
        Transaction(
            lane_id=3,
            signal_state="GREEN",
            vehicle_count=20,
            green_time=60,
            emergency_vehicle=True,  # Emergency vehicle!
            node_id="example_node"
        ),
    ]
    
    for i, tx in enumerate(transactions, 1):
        print(f"   {i}. Lane {tx.lane_id}: {tx.signal_state} (vehicles: {tx.vehicle_count})")
        blockchain.add_transaction(tx)
        time.sleep(0.5)  # Small delay for demo
    
    print(f"   ✓ Added {len(transactions)} transactions")
    print(f"   ✓ Pending transactions: {len(blockchain.pending_transactions)}")
    print()
    
    # Mine the block (should trigger automatically since block_size=3)
    print("3. Mining block...")
    print("   Mining block with proof-of-work (difficulty=2)...")
    mined_block = blockchain.mine_pending_transactions()
    
    if mined_block:
        print(f"   ✓ Block #{mined_block.index} mined successfully!")
        print(f"   ✓ Block hash: {mined_block.hash}")
        print(f"   ✓ Nonce: {mined_block.nonce}")
        print(f"   ✓ Transactions in block: {len(mined_block.transactions)}")
        print()
    
    # Add more transactions to demonstrate multiple blocks
    print("4. Adding more transactions for second block...")
    more_transactions = [
        Transaction(lane_id=4, signal_state="GREEN", vehicle_count=12, 
                   green_time=48, emergency_vehicle=False, node_id="example_node"),
        Transaction(lane_id=1, signal_state="RED", vehicle_count=5, 
                   green_time=37, emergency_vehicle=False, node_id="example_node"),
    ]
    
    for tx in more_transactions:
        print(f"   - Lane {tx.lane_id}: {tx.signal_state}")
        blockchain.add_transaction(tx)
    
    print(f"   ✓ Added {len(more_transactions)} more transactions")
    print()
    
    # Manually mine since we have 2 transactions (block_size is 3)
    print("5. Mining second block manually...")
    mined_block2 = blockchain.mine_pending_transactions()
    if mined_block2:
        print(f"   ✓ Block #{mined_block2.index} mined!")
    print()
    
    # Display blockchain statistics
    print("6. Blockchain Statistics:")
    print("   " + "-" * 56)
    stats = blockchain.get_statistics()
    for key, value in stats.items():
        if key != 'lane_transactions':  # Handle separately
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n   Lane Transaction Counts:")
    for lane_id, count in stats['lane_transactions'].items():
        print(f"      Lane {lane_id}: {count} transactions")
    print()
    
    # Validate blockchain
    print("7. Validating blockchain integrity...")
    is_valid = blockchain.is_chain_valid()
    print(f"   ✓ Blockchain is {'VALID' if is_valid else 'INVALID'}")
    print()
    
    # Get transactions for a specific lane
    print("8. Querying lane-specific transactions...")
    lane_1_txs = blockchain.get_transactions_by_lane(lane_id=1)
    print(f"   Lane 1 has {len(lane_1_txs)} transactions:")
    for tx in lane_1_txs:
        print(f"      - {tx.signal_state}: {tx.vehicle_count} vehicles at {tx.timestamp[:19]}")
    print()
    
    # Get latest state for a lane
    print("9. Getting latest signal state...")
    latest = blockchain.get_latest_signal_state(lane_id=1)
    if latest:
        print(f"   Latest state for Lane 1:")
        print(f"      Signal: {latest.signal_state}")
        print(f"      Vehicles: {latest.vehicle_count}")
        print(f"      Green Time: {latest.green_time}s")
        print(f"      Emergency: {'Yes' if latest.emergency_vehicle else 'No'}")
    print()
    
    # Display blockchain structure
    print("10. Blockchain Structure:")
    print("    " + "-" * 56)
    for i, block in enumerate(blockchain.chain):
        print(f"    Block #{block.index}:")
        print(f"      Hash: {block.hash[:32]}...")
        print(f"      Previous: {block.previous_hash[:32]}...")
        print(f"      Transactions: {len(block.transactions)}")
        print(f"      Nonce: {block.nonce}")
        print()
    
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    print("\nThe blockchain is now ready to record real traffic signal changes.")
    print("All transactions are cryptographically secured and tamper-proof.")

if __name__ == "__main__":
    main()


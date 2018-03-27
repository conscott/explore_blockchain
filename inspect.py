#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from rpc import NodeCLI

# 1 BTC = 10^8 Satoshi
COIN = 10**8

# RPC proxy
rpc = NodeCLI(os.getenv("BITCOINCLI", "bitcoin-cli"))

# Can inspect in browser
URL_SCHEME = "https://blockchain.info/tx/{}"

# Parse arguments
parser = argparse.ArgumentParser(add_help=True,
                                 usage='%(prog)s [options]',
                                 description='A tool to inspect bitcoin transactions',
                                 epilog='''Help text and arguments for individual test script:''',
                                 formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('--gt', type=int, default=5000, help='List txs with output greater than this value (in BTC)')
parser.add_argument('--veramt', type=float, default=0.1, help='Assume verify transaction is less than value (in BTC)')
parser.add_argument('--maxblocks', type=int, default=1000, help='Maximum number of blocks to scan')
parser.add_argument('--maxdepth', type=int, default=1, help='Maximum depth of back-scan')
args, unknown_args = parser.parse_known_args()

if unknown_args:
    print("Unknown args: %s...Try" % unknown_args)
    print("./draw_mempool.py --help")
    sys.exit(0)


# Kick off a tab open to further inspect tx
def follow_link(tx):
    url = URL_SCHEME.format(tx)
    cmd = "python -m webbrowser -t %s" % url
    FNULL = open(os.devnull, 'w')
    subprocess.call(cmd.split(), stdout=FNULL, stderr=subprocess.STDOUT)


# If found a tx with a large output, see if inputs are linked to previous tx
# with tiny output, make function recursive to explore depth
def back_scan(txinfo, verify_tx_amount, depth):
    print("Back-scanning %s Inputs" % len(txinfo['vin']))
    for vin in txinfo['vin']:
        spent_txid = vin['txid']
        vout_spent = vin['vout']
        spent_tx = rpc.getrawtransaction(spent_txid, 'true')
        for vout in spent_tx['vout']:
            if vout['value'] <= verify_tx_amount:
                print("Microtransaction deposited to %s" % vout['scriptPubKey']['addresses'])
                return True
    return False


# If tx has been seen in backscan before, can skip
seen_txs = set()
current_block = rpc.getblockcount()
for block_height in range(current_block, current_block-args.maxblocks, -1):
    block_hash = rpc.getblockhash(block_height)
    txs = rpc.getblock(block_hash)['tx']
    print("Inspecting block %s with %s txs" % (block_hash, len(txs)))
    # Scan each tx in recent blocks
    for tx in txs:
        print("Inspect %s" % tx)
        txinfo = rpc.getrawtransaction(tx, 'true')
        # Scan outputs of each transaction
        for vout in txinfo['vout']:
            if vout['value'] > args.gt:
                print("Inspecting tx %s with output of %s BTC" % (tx, vout['value']))
                seen_txs.add(tx)
                if back_scan(tx, args.veramt, args.maxdepth):
                    print("Tx %s is a winner!" % tx)
                    follow_link(tx)
                    sys.exit(0)

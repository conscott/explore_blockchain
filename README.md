#### Description
WIP tool to inspect blockchain transactions and look for certain sequences. Requires a connection to a full node with a full transcation index (`-txindex=1`)

Example: Find transactions with an output greater than or equal to 1000 BTC, having an input with previous microtransaction of < 0.01
The chain would indicate a "proof of ownership tx" before a large OTC trade
```
./inspect --gt=1000 --veramt=0.001
```

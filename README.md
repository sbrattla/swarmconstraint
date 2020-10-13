## Use Case

You run a Docker Swarm across multiple data centers (DCs). You prefer a service to primarily run in one of the DCs, but are willing to accept different placements if the preferred DCs becomes unavailable.

This application will watch node availability. If the watched nodes becomes unavailable, the application will disable one
or more specified labels to ensure that constrained services will be scheduled.

## Example

### Nodes

|DC   |Node |Labels          |
|-----|-----|----------------|
|DC1  |node1|                |
|DC2  |node2|secondary=true  |
|DC3  |node3|secondary=true  |

### Service
    "Labels": {
       "secondary": "true"
       
### Work

    user@node2:~$ swarmconstraint --watch node1 --toggle node2 --label secondary
 


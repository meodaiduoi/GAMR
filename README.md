# GAMR: An Enhanced Non-dominated Sorting Genetic Algorithm II-based Dynamic multi-objective QoS routing in Software-Defined Networks
Routing optimization plays a crucial role in traffic engineering, aiming to efficiently allocate network resources to meet various service requirements. In dynamic network environments, however, network configurations constantly change, therefore single-objective routing faces numerous challenges in managing multiple concurrent demands. Moreover, the complexity of the problem increases as end-to-end Quality of Service (QoS) requirements and conflicts between them accumulate. Several approaches have been proposed to address this issue, but most of them fall into the stability-plasticity dilemma or involve excessive computation or convergence times in practical implementations. \textcolor{blue}{We introduce a dynamic multi-objective QoS routing approach based on NSGA-II (Non-dominated Sorting Genetic Algorithm II), called GAMR, utilizing QoS metrics to construct a multi-objective function.} By proposing new initialization and crossover strategies, our solution can find optimal solutions within a short runtime. Additionally, The GAMR application is deployed on the control plane within Software-Defined Networks (SDNs) and evaluated against benchmark methods under various settings. Compared to multi-objective algorithms, the proposed method demonstrates significant improvements in performance indicators. It shows enhancements ranging from 3.4\% to 22.8\% on the Hypervolume (HV) metric and from  33\% to 86\% on the Inverted Generational Distance (IGD) metric. Regarding the objectives, the experimental results demonstrate that our method reduces the forwarding delay and packet loss rate to 41.25ms and 3.9\%, respectively, under the most challenging network configuration scenario (with only 2 servers and up to 100 requests) on the Chinanet network (44 nodes).

### Requirements

The project requires the following Python libraries:

* `ryu`
* `fastapi[all]`
* `mininet`
* `networkx`
* `numpy`
* `requests`

### Project Structure

The project is organized into four main modules:

* `dynamicsdn`: Contains the NSGA-II implementation and Dijkstra's algorithm for path selection.
* `scenario`: Stores different scenarios for automated testing.
* `sdndb`: Provides a database for storing network information and routing results.
* `mn_restapi`: Implements a REST API hook for interacting with Mininet scripts.

### Startup Instructions

1. **Set environment variable:** Before starting the application, add the parent directory of the project to your Python path. In your terminal, run:

```bash
export PYTHONPATH={parent directory of project}
```

2. **Start application:** Run the following command to start both Ryu and the application:

```bash
./startup.py
```

### Further Information

* For detailed documentation, please refer to the project's internal documentation.
* Feel free to open issues on GitHub for any questions or feedback.

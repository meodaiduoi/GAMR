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

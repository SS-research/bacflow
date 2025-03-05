## usage

```bash
streamlit run webapp.py
```

# BACflow

BACflow is a Python library for estimating Blood Alcohol Concentration (BAC) using advanced simulation models inspired by Widmark's formula and subsequent research. It supports dynamic modeling of alcohol absorption and elimination kinetics through efficient, vectorized computations and is designed to integrate easily with user interfaces (e.g., Streamlit apps) or command-line tools.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Example](#basic-example)
  - [API Overview](#api-overview)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact](#contact)

---

## Features

- **Dynamic Alcohol Absorption:**  
  Incorporates food intake data to adjust the alcohol absorption halflife dynamically on a 6-to-18 minute scale.
  
- **Flexible Simulation:**  
  Supports user-defined simulation bounds (start/end times), initial absorption levels, and variable time-step (granularity) for accurate modeling.
  
- **Multiple Models:**  
  Implements a range of BAC estimation models (e.g., Seidl, Widmark, Forrest, Watson, Ulrich, and an average model) with an aggregation function to compute mean and variance across models.
  
- **Threshold Identification:**  
  Provides functions to determine key milestones such as when the BAC drops below a driving limit or reaches zero permanently.
  
- **Efficient Computations:**  
  Built with NumPy and Pandas to leverage vectorized operations for high-performance simulations.

- **Modular Design:**  
  Separates core BAC computations from user interface concerns, enabling integration with various frontends or applications.

---

## Installation

Install BACflow using pip (Python 3.8+ is recommended):

```bash
pip install bacflow
```

Alternatively, clone the repository and install locally:

```bash
git clone https://github.com/yourusername/bacflow.git
cd bacflow
pip install .
```

---

## Usage

### Basic Example

Below is a simple example to simulate BAC from a list of drinks using a single model:

```python
from datetime import datetime, timedelta, timezone
from bacflow.schemas import Drink, Person, Model, Sex
from bacflow.simulation import simulate, aggregate_simulation_results, identify_threshold_times

# Define simulation parameters
start_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
end_time = start_time + timedelta(hours=2)
dt = 60  # 1-minute time step
default_halflife = 720  # default halflife in seconds (12 minutes)
initial_alc = 0.0

# Create a sample drink list
drink1 = Drink(
    name="Beer",
    vol=0.33,           # in liters
    alc_prop=0.05,      # 5% alcohol
    time=start_time + timedelta(minutes=10),
    sip_interval=1
)
drinks = [drink1]

# Create a sample person
person = Person(age=30, height=1.75, weight=70, sex=Sex.M)

# Simulate using a selected model (e.g., Seidl)
sim_models = [Model.Seidl]
sim_results = simulate(drinks, person, start_time, end_time, dt, default_halflife, initial_alc, sim_models)

# Aggregate results if multiple models are simulated
aggregated = aggregate_simulation_results(sim_results)

# Identify key threshold times (e.g., driving limit of 0.02 g/dL)
driving_limit = 0.02
drive_safe_time, sober_time = identify_threshold_times(aggregated, driving_limit)

print("Drive Safe Time:", drive_safe_time)
print("Sober Time:", sober_time)
```

### API Overview

- **`cumulative_absorption(drinks, start_time, end_time, dt, default_halflife, food_intakes, initial_alc)`**  
  Computes a time series of cumulative alcohol absorption in kg based on dynamic food intake and default halflife.

- **`simulate(drinks, person, start_time, end_time, dt, default_halflife, initial_alc, simulation, food_intakes)`**  
  Runs the BAC simulation using specified models and returns a dictionary mapping each model to its time series of BAC values.

- **`aggregate_simulation_results(sim_results)`**  
  Aggregates multiple simulation outputs into a single time series with computed mean and variance.

- **`identify_threshold_times(aggregated_ts, driving_limit, tolerance)`**  
  Determines the first time when the BAC falls below the driving limit and the first time it becomes permanently zero.

- **Modeling functions in `modeling.py`:**  
  Include various body factor calculations and elimination kinetics based on different models (e.g., Seidl, Widmark).

- **Plotting functions in `plotting.py`:**  
  Visualize simulation results with confidence bands and threshold markers.

For more detailed API documentation, please refer to the [Documentation](https://github.com/yourusername/bacflow/docs).

---

## Testing

BACflow includes a comprehensive test suite using Pytest. To run tests, simply execute:

```bash
pytest
```

This will run tests covering the key functions and ensure that the library behaves as expected.

---

## Contributing

Contributions are welcome! If you'd like to contribute to BACflow, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Write tests to cover your changes.
4. Ensure that the test suite passes.
5. Submit a pull request describing your changes and why they are needed.

For major changes, please open an issue first to discuss what you would like to change.

---

## License

BACflow is released under the [MIT License](LICENSE).

---

## Acknowledgements

BACflow was inspired by the foundational work of Widmark and further studies on alcohol metabolism. Special thanks to the contributors and the open-source community for their insights and support.

---

## Contact

For any questions or feedback, please reach out via:

- GitHub Issues: [https://github.com/yourusername/bacflow/issues](https://github.com/yourusername/bacflow/issues)
- Email: your.email@example.com

---

Happy simulating!

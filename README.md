# Alpha Efficiency Calculator

An interactive, open-source web application for calculating gross alpha counting efficiency based on an analytical framework that integrates alpha self-absorption and backscattering models.

> **Reference:** The theoretical framework behind this software is based on the research paper *"MATRIX EFFECTS ON GROSS ALPHA DETERMINATION IN ENVIRONMENTAL WATER RESIDUES: AN ANALYTICAL FRAMEWORK BASED ON EFFECTIVE ALPHA-PARTICLE MASS RANGE"* authored by Lê Đình Hùng et al. (under review).

## Features
- Computes total efficiency, direct escape probability, and backscattering components across different kinetic regions (Region A, B, and C).
- Interactive Matrix Database for effective alpha-particle mass ranges (Rmix) with local persistence.
- Customizable parameters for sample dimensions, mass, detector geometry, and alpha-particle energies.

## Installation & Local Running

1. Clone the repository, install dependencies, and run the app:
   ```bash
   git clone https://github.com/ledinhhung0889/Alpha-Calculator.git
   cd Alpha-Calculator
   pip install -r requirements.txt
   streamlit run app.py
   ```

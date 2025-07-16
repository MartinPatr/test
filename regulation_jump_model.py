import pandas as pd
import numpy as np


def ei_gap_adjustmen_factor(ei_gap, 
threshold=0.0, 
gap_sensitivity=0.03):
    """
    Computes a linear adjustment factor based on the EI Gap.
    - ei_gap: Energy Intensity Gap (positive = non-compliant)
    - threshold: baseline EI Gap for no adjustment
    - gap_sensitivity: sensitivity coefficient for EI Gap
    """
    if ei_gap <= threshold:
        return 1.0  
    return min(1.0 + gap_sensitivity * ei_gap, 4)

def heating_source_adjustment_factor(heating_source, 
heating_factor_fossil=1.75, 
heating_factor_mixed=1.25, 
heating_factor_electric=1.0):
    """
    Computes a multiplier based on the heating source.
    - heating_source: 'fossil', 'mixed', or 'electric'
    """
    if heating_source.lower() == 'fossil':
        return heating_factor_fossil  # High risk for fossil fuels
    elif heating_source.lower() == 'mixed':
        return heating_factor_mixed  # Moderate risk for mixed sources
    else:
        return heating_factor_electric  # Electric has no additional risk

def certification_adjustment_factor(cert_level, 
cert_factor_a=0.1, 
cert_factor_b=0.4, 
cert_factor_c=0.9):
    """
    Computes a discount factor based on the certification level.
    - cert_level: 'A', 'B', or 'C'
    - cert_factor_a: discount factor for 'A' level
    - cert_factor_b: discount factor for 'B' level
    - cert_factor_c: discount factor for 'C' level (or lower)
    """
    if cert_level == 'A':
      return cert_factor_a  
    elif cert_level == 'B':
        return cert_factor_b  
    elif cert_level == 'C':
        return cert_factor_c
    else:
        return 1.0  

def size_adjustment_factor(size_ft2, 
reference_size=4600, 
sensitivty=0.25):
    """
    Computes a log-based size adjustment factor for jump risk.
    - size_ft2: building size in ft²
    - reference_size: policy threshold baseline
    - sensitivty: sensitivity coefficient
    """
    if size_ft2 < reference_size:
        return 1.0  # No boost below threshold
    log_term = np.log10(size_ft2 / reference_size)
    return 1.0 + sensitivty * log_term


def calc_jump_rate(ei_gap, heating_source, cert_level, size_m2, 
base_rate=0.02):
    """
    Calculate annual regulatory jump rate (λ) for a building based on:
    - ei_gap: EI Gap relative to CRREM target (positive = non-compliant)
    - heating_source: 'fossil', 'mixed', or 'electric'
    - cert_level: 'A', 'B', or 'C'
    - size_m2: building size in square meters (not used in this version)
    """
    # Calculate the EI Gap adjustment factor
    gap_factor = ei_gap_adjustmen_factor(ei_gap)
    # print(f"EI Gap Adjustment Factor: {gap_factor:.3f}")

    # Calculate the heating source adjustment factor
    heating_factor = heating_source_adjustment_factor(heating_source)
    # print(f"Heating Source Adjustment Factor: {heating_factor:.3f}")

    # Calculate the certification adjustment factor
    cert_factor = certification_adjustment_factor(cert_level)
    # print(f"Certification Adjustment Factor: {cert_factor:.3f}")

    # Calculate size adjustment factor
    size_factor = size_adjustment_factor(size_m2)
    # print(f"Size Adjustment Factor: {size_factor:.3f}")

    # Calculate the jump rate
    rate = base_rate * gap_factor * heating_factor * cert_factor * size_factor

    # Cap rate between 0 and 1
    return min(max(rate, 0.0), 1.0)


if __name__ == "__main__":
  # 1️⃣ Load the CRREM pathway
  crrem_df = pd.read_csv("/Users/martinpatrouchev/Desktop/Work/RBC Amplify/crrem_pathways.csv")

  # 2️⃣ Assume actual constant EI for building
  actual_ei = 160
  scenario = "1.5c"
  property_type = "Office"
  heating_source = 'fossil'
  cert_level = 'NA'
  size_m2 = 10000  


  # 4️⃣ Store results
  jump_rates = []
  ei_gaps = []

  for idx, row in crrem_df[crrem_df['Scenario'] == scenario].iterrows():
      year = row['Year']

      target_ei = row[property_type]
      # Calculate EI Gap
      ei_gap = actual_ei - target_ei
      ei_gaps.append(ei_gap)
      
      # Calculate Jump Rate
      jump_rate = calc_jump_rate(
          ei_gap,
          heating_source,
          cert_level,
          size_m2
      )
      jump_rates.append(jump_rate)
      print(f"Year {year}: Target EI={target_ei}, EI Gap={ei_gap:.1f}, Jump Rate={jump_rate:.3f}")

  # 5️⃣ Calculate expected number of jumps over 25 years
  expected_jumps_25yrs = sum(jump_rates)
  n_simulations = 1000
  jump_counts = []

  for _ in range(n_simulations):
      jumps_this_run = np.random.binomial(1, jump_rates)
      jump_counts.append(sum(jumps_this_run))

  print("max",max(jump_counts), " min", min(jump_counts))
  print(f"Total Expected Regulatory Events over 25 years: {expected_jumps_25yrs:.2f}")
  print(f"Simulated Mean Jumps: {np.mean(jump_counts):.2f}")
  print(f"Simulated Std Dev of Jumps: {np.std(jump_counts):.2f}")

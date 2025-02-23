import 'dart:math';
import 'dart:convert';

/// Utility functions

double mean(List<double> values) =>
    values.isEmpty ? 0 : values.reduce((a, b) => a + b) / values.length;

double std(List<double> values) {
  double m = mean(values);
  double sumSq = values.map((v) => pow(v - m, 2)).reduce((a, b) => a + b);
  return sqrt(sumSq / values.length);
}

/// Computes the qth quantile (q between 0 and 1) of a sorted list.
double quantile(List<double> sortedValues, double q) {
  if (sortedValues.isEmpty) return 0;
  int index = ((sortedValues.length - 1) * q).round();
  return sortedValues[index];
}

/// Returns the covariance of two lists.
double covariance(List<double> xs, List<double> ys) {
  if (xs.length != ys.length || xs.isEmpty) return 0;
  double mX = mean(xs);
  double mY = mean(ys);
  double sum = 0;
  for (int i = 0; i < xs.length; i++) {
    sum += (xs[i] - mX) * (ys[i] - mY);
  }
  return sum / xs.length;
}

/// Returns the determinant of a 2x2 matrix.
double det2x2(double a, double b, double c, double d) => a * d - b * c;

//
// Data structures and basic pipeline functions
//

/// In our case, we assume sensor data is provided as a List of Maps,
/// where each Map represents a row with keys like 'timestamp', 'acc_x_smartphone', etc.
typedef SensorRow = Map<String, dynamic>;

/// Fills missing values using forward fill.
List<SensorRow> loadAndPreprocessData(List<SensorRow> data, {String fillMethod = 'ffill'}) {
  // Simple forward fill implementation (assumes keys are present in all rows).
  Map<String, dynamic> lastSeen = {};
  for (var row in data) {
    row.forEach((key, value) {
      if (value == null && lastSeen.containsKey(key)) {
        row[key] = lastSeen[key];
      } else if (value != null) {
        lastSeen[key] = value;
      }
    });
  }
  return data;
}

/// Normalizes numeric columns (Z-score) and removes rows with any value below the 1st
/// or above the 99th percentile.
List<SensorRow> normalizeAndRemoveOutliers(List<SensorRow> data) {
  if (data.isEmpty) return data;
  // Get list of numeric keys (exclude timestamp)
  List<String> keys = data.first.keys.where((k) => k != 'timestamp').toList();
  // Compute mean and std for each key
  Map<String, double> means = {};
  Map<String, double> stds = {};
  for (var key in keys) {
    List<double> col =
        data.map((row) => (row[key] as num).toDouble()).toList();
    means[key] = mean(col);
    stds[key] = std(col);
  }
  // Normalize each row
  List<SensorRow> normalized = [];
  for (var row in data) {
    SensorRow newRow = Map.from(row);
    bool valid = true;
    for (var key in keys) {
      double value = (row[key] as num).toDouble();
      double z = stds[key]! > 0 ? (value - means[key]!) / stds[key]! : 0;
      newRow[key] = z;
    }
    normalized.add(newRow);
  }
  // For each column, compute 1% and 99% quantile over normalized data.
  Map<String, double> lowerBounds = {};
  Map<String, double> upperBounds = {};
  for (var key in keys) {
    List<double> col =
        normalized.map((row) => row[key] as double).toList()..sort();
    lowerBounds[key] = quantile(col, 0.01);
    upperBounds[key] = quantile(col, 0.99);
  }
  // Filter out rows that have any column outside bounds.
  return normalized.where((row) {
    for (var key in keys) {
      double value = row[key] as double;
      if (value < lowerBounds[key]! || value > upperBounds[key]!) return false;
    }
    return true;
  }).toList();
}

/// Segments data into windows of fixed seconds (adds 'window_id' field).
List<SensorRow> segmentData(List<SensorRow> data, {int windowSizeSeconds = 5}) {
  if (data.isEmpty) return data;
  // Convert timestamps and compute seconds since start.
  DateTime startTime = DateTime.parse(data.first['timestamp']);
  for (var row in data) {
    DateTime ts = DateTime.parse(row['timestamp']);
    double secondsSinceStart = ts.difference(startTime).inMilliseconds / 1000.0;
    row['seconds_since_start'] = secondsSinceStart;
    row['window_id'] = (secondsSinceStart ~/ windowSizeSeconds);
  }
  return data;
}

//
// Feature computation functions
//

double calculateConfidenceEllipseArea(List<double> x, List<double> y, {double confidence = 0.95}) {
  double covXY = covariance(x, y);
  double covXX = covariance(x, x);
  double covYY = covariance(y, y);
  double det = det2x2(covXX, covXY, covXY, covYY);
  // For chi-square quantile, approximate with fixed value for 2 df and 95% confidence.
  // chi2.ppf(0.95, 2) ≈ 5.991
  double chi2Val = 5.991;
  return pi * chi2Val * sqrt(det.abs());
}

double calculateSwayVolume(List<double> x, List<double> y, List<double> z, {double confidence = 0.95}) {
  int n = x.length;
  List<List<double>> points = List.generate(n, (i) => [x[i], y[i], z[i]]);
  // Compute mean (center)
  List<double> center = [0.0, 0.0, 0.0];
  for (var p in points) {
    center[0] += p[0];
    center[1] += p[1];
    center[2] += p[2];
  }
  center = center.map((v) => v / n).toList();
  // Compute distances from center
  List<double> distances = points.map((p) =>
      sqrt(pow(p[0] - center[0], 2) + pow(p[1] - center[1], 2) + pow(p[2] - center[2], 2))
  ).toList();
  distances.sort();
  double r = quantile(distances, 0.95);
  return (4 / 3) * pi * pow(r, 3);
}

/// Computes magnitude (Euclidean norm) for each row of a list of lists.
List<double> computeMagnitude(List<List<double>> vectors) {
  return vectors.map((v) => sqrt(v.map((x) => x * x).reduce((a, b) => a + b))).toList();
}

/// Simple peak detection: returns indices of peaks where value is greater than its immediate neighbors
List<int> findPeaks(List<double> values, double threshold) {
  List<int> peaks = [];
  for (int i = 1; i < values.length - 1; i++) {
    if (values[i] > threshold &&
        values[i] > values[i - 1] &&
        values[i] > values[i + 1]) {
      peaks.add(i);
    }
  }
  return peaks;
}

/// Calculates gait features: steps, cadence, and returns detected peak indices.
Map<String, dynamic> calculateGaitFeatures(List<List<double>> accData, {int frequency = 50}) {
  List<double> mags = computeMagnitude(accData);
  double m = mean(mags);
  double s = std(mags);
  double threshold = m + s;
  List<int> peaks = findPeaks(mags, threshold);
  int steps = peaks.length;
  double durationMinutes = (accData.length / frequency) / 60.0;
  double cadence = durationMinutes > 0 ? steps / durationMinutes : 0;
  return {'steps': steps, 'cadence': cadence, 'peaks': peaks};
}

/// Computes skewness and kurtosis.
Map<String, double> calculateStatisticalFeatures(List<double> data) {
  int n = data.length;
  if (n == 0) return {'skewness': 0, 'kurtosis': 0};
  double m = mean(data);
  double s = std(data);
  double skewness = data.map((x) => pow((x - m) / s, 3)).reduce((a, b) => a + b) / n;
  double kurtosis = data.map((x) => pow((x - m) / s, 4)).reduce((a, b) => a + b) / n - 3;
  return {'skewness': skewness, 'kurtosis': kurtosis};
}

/// Stub for Total Harmonic Distortion (THD); a proper FFT-based implementation is recommended.
double calculateHarmonics(List<double> data) {
  // For now, return 0.
  return 0;
}

/// Detrends a signal by subtracting its mean.
List<double> detrend(List<double> data) {
  double m = mean(data);
  return data.map((x) => x - m).toList();
}

/// Cumulative trapezoidal integration.
List<double> cumTrapz(List<double> data, double dt) {
  List<double> integrated = List.filled(data.length, 0.0);
  for (int i = 1; i < data.length; i++) {
    integrated[i] = integrated[i - 1] + ((data[i - 1] + data[i]) / 2) * dt;
  }
  return integrated;
}

/// Calculates average gait velocity and residual step length from a 1D acceleration signal.
Map<String, double> calculateVelocityAndResidual(List<double> accSignal, {int frequency = 50}) {
  double dt = 1 / frequency;
  List<double> accDetrended = detrend(accSignal);
  List<double> velocity = cumTrapz(accDetrended, dt);

  List<int> peaks = findPeaks(accSignal, mean(accSignal) + std(accSignal));
  if (peaks.length < 2) return {'avgVelocity': 0, 'residualStepLength': 0};

  List<double> stepLengths = [];
  for (int i = 1; i < peaks.length; i++) {
    int start = peaks[i - 1];
    int end = peaks[i];
    // Compute displacement over the step interval.
    double displacement = 0;
    for (int j = start; j < end - 1; j++) {
      displacement += ((velocity[j] + velocity[j + 1]) / 2) * dt;
    }
    stepLengths.add(displacement);
  }
  double avgStepLength = mean(stepLengths);
  double residual = stepLengths.map((v) => (v - avgStepLength).abs()).reduce((a, b) => a + b) / stepLengths.length;
  double totalDisplacement = velocity.last;
  double totalTime = accSignal.length * dt;
  double avgVelocity = totalTime > 0 ? totalDisplacement / totalTime : 0;
  return {'avgVelocity': avgVelocity, 'residualStepLength': residual};
}

/// Calculates average step time and its residual from a 1D acceleration signal.
Map<String, double> calculateStepTimeFeatures(List<double> accSignal, {int frequency = 50}) {
  double dt = 1 / frequency;
  List<int> peaks = findPeaks(accSignal, mean(accSignal) + std(accSignal));
  if (peaks.length < 2) return {'avgStepTime': 0, 'residualStepTime': 0};
  List<double> stepIntervals = [];
  for (int i = 1; i < peaks.length; i++) {
    stepIntervals.add((peaks[i] - peaks[i - 1]) * dt);
  }
  double avgStepTime = mean(stepIntervals);
  double residual = stepIntervals.map((t) => (t - avgStepTime).abs()).reduce((a, b) => a + b) / stepIntervals.length;
  return {'avgStepTime': avgStepTime, 'residualStepTime': residual};
}

/// Cumulative integration to compute mean and variance of velocity signals.
Map<String, double> calculateVelocityFeatures(Map<String, List<double>> accData, {int frequency = 50}) {
  double dt = 1 / frequency;
  List<double> vx = cumTrapz(accData['acc_x']!, dt);
  List<double> vy = cumTrapz(accData['acc_y']!, dt);
  List<double> vz = cumTrapz(accData['acc_z']!, dt);
  return {
    'meanX': mean(vx),
    'varX': std(vx) * std(vx),
    'meanY': mean(vy),
    'varY': std(vy) * std(vy),
    'meanZ': mean(vz),
    'varZ': std(vz) * std(vz),
  };
}

/// Cumulative integration for angular velocity signals.
Map<String, double> calculateAngularVelocityFeatures(Map<String, List<double>> gyroData, {int frequency = 50}) {
  double dt = 1 / frequency;
  List<double> wx = cumTrapz(gyroData['gyro_x']!, dt);
  List<double> wy = cumTrapz(gyroData['gyro_y']!, dt);
  List<double> wz = cumTrapz(gyroData['gyro_z']!, dt);
  return {
    'meanX': mean(wx),
    'varX': std(wx) * std(wx),
    'meanY': mean(wy),
    'varY': std(wy) * std(wy),
    'meanZ': mean(wz),
    'varZ': std(wz) * std(wz),
  };
}

/// Calculates all combined high-level features from a segmented window of data.
/// Assumes that `df` is a list of SensorRow maps representing one window.
Map<String, double> calculateCombinedFeatures(List<SensorRow> df) {
  // Extract smartphone accelerometer data as list of [x, y, z]
  List<List<double>> smartphoneAcc = df.map((row) => [
        (row['acc_x_smartphone'] as num).toDouble(),
        (row['acc_y_smartphone'] as num).toDouble(),
        (row['acc_z_smartphone'] as num).toDouble()
      ]).toList();

  var gait = calculateGaitFeatures(smartphoneAcc, frequency: 50);
  int steps = gait['steps'];
  double cadence = gait['cadence'];

  // Use smartphone acc_z for velocity and step timing features.
  List<double> smartphoneAccZ = df.map((row) => (row['acc_z_smartphone'] as num).toDouble()).toList();
  var velRes = calculateVelocityAndResidual(smartphoneAccZ, frequency: 50);
  var stepTimes = calculateStepTimeFeatures(smartphoneAccZ, frequency: 50);

  // For velocity features over all axes (smartphone)
  List<double> accX = df.map((row) => (row['acc_x_smartphone'] as num).toDouble()).toList();
  List<double> accY = df.map((row) => (row['acc_y_smartphone'] as num).toDouble()).toList();
  List<double> accZ = smartphoneAccZ;
  Map<String, List<double>> smartphoneAccMap = {
    'acc_x': accX,
    'acc_y': accY,
    'acc_z': accZ,
  };
  Map<String, double> velocityFeats = calculateVelocityFeatures(smartphoneAccMap, frequency: 50);

  // Gyroscope-based sway features for smartphone
  List<double> gyroX = df.map((row) => (row['gyro_x_smartphone'] as num).toDouble()).toList();
  List<double> gyroY = df.map((row) => (row['gyro_y_smartphone'] as num).toDouble()).toList();
  List<double> gyroZ = df.map((row) => (row['gyro_z_smartphone'] as num).toDouble()).toList();
  double XYSway = calculateConfidenceEllipseArea(gyroX, gyroY);
  double YZSway = calculateConfidenceEllipseArea(gyroY, gyroZ);
  double XZSway = calculateConfidenceEllipseArea(gyroX, gyroZ);
  double swayVolume = calculateSwayVolume(gyroX, gyroY, gyroZ);

  // Additional statistical and frequency features on acc_z (smartphone)
  double freqRatio = 0; // You would implement a Welch method here.
  double bandPower = smartphoneAccZ.reduce((a, b) => a + b); // Stub
  double snr = smartphoneAccZ.isEmpty ? 0 : 10 * log( (pow(mean(smartphoneAccZ),2)) / (pow(std(smartphoneAccZ),2)) ) / ln10;
  var stats = calculateStatisticalFeatures(smartphoneAccZ);
  double thd = calculateHarmonics(smartphoneAccZ);

  // Smartwatch features: accelerometer velocity
  List<double> swAccX = df.map((row) => (row['acc_x_smartwatch'] as num).toDouble()).toList();
  List<double> swAccY = df.map((row) => (row['acc_y_smartwatch'] as num).toDouble()).toList();
  List<double> swAccZ = df.map((row) => (row['acc_z_smartwatch'] as num).toDouble()).toList();
  Map<String, List<double>> swAccMap = {
    'acc_x': swAccX,
    'acc_y': swAccY,
    'acc_z': swAccZ,
  };
  Map<String, double> velocityFeatsSW = calculateVelocityFeatures(swAccMap, frequency: 50);

  // Smartwatch features: gyroscope angular velocity
  List<double> swGyroX = df.map((row) => (row['gyro_x_smartwatch'] as num).toDouble()).toList();
  List<double> swGyroY = df.map((row) => (row['gyro_y_smartwatch'] as num).toDouble()).toList();
  List<double> swGyroZ = df.map((row) => (row['gyro_z_smartwatch'] as num).toDouble()).toList();
  Map<String, List<double>> swGyroMap = {
    'gyro_x': swGyroX,
    'gyro_y': swGyroY,
    'gyro_z': swGyroZ,
  };
  Map<String, double> angularVelocityFeats = calculateAngularVelocityFeatures(swGyroMap, frequency: 50);

  // Gyroscope-based sway features for smartwatch
  double XYSwaySW = calculateConfidenceEllipseArea(swGyroX, swGyroY);
  double YZSwaySW = calculateConfidenceEllipseArea(swGyroY, swGyroZ);
  double XZSwaySW = calculateConfidenceEllipseArea(swGyroX, swGyroZ);
  double swayVolumeSW = calculateSwayVolume(swGyroX, swGyroY, swGyroZ);

  return {
    // Smartphone features
    'steps_smartphone': steps.toDouble(),
    'cadence_smartphone': cadence,
    'avg_velocity_smartphone': velRes['avgVelocity']!,
    'residual_step_length_smartphone': velRes['residualStepLength']!,
    'avg_step_time_smartphone': stepTimes['avgStepTime']!,
    'residual_step_time_smartphone': stepTimes['residualStepTime']!,
    'XY_sway_area_smartphone': XYSway,
    'YZ_sway_area_smartphone': YZSway,
    'XZ_sway_area_smartphone': XZSway,
    'sway_volume_smartphone': swayVolume,
    'frequency_ratio_smartphone': freqRatio,
    'band_power_smartphone': bandPower,
    'signal_noise_ratio_smartphone': snr,
    'skewness_smartphone': stats['skewness']!,
    'kurtosis_smartphone': stats['kurtosis']!,
    'total_harmonic_distortion_smartphone': thd,
    'velocity_mean_X_smartphone': velocityFeats['meanX']!,
    'velocity_variance_X_smartphone': velocityFeats['varX']!,
    'velocity_mean_Y_smartphone': velocityFeats['meanY']!,
    'velocity_variance_Y_smartphone': velocityFeats['varY']!,
    'velocity_mean_Z_smartphone': velocityFeats['meanZ']!,
    'velocity_variance_Z_smartphone': velocityFeats['varZ']!,
    // Smartwatch features
    'XY_sway_area_smartwatch': XYSwaySW,
    'YZ_sway_area_smartwatch': YZSwaySW,
    'XZ_sway_area_smartwatch': XZSwaySW,
    'sway_volume_smartwatch': swayVolumeSW,
    'velocity_mean_X_smartwatch': velocityFeatsSW['meanX']!,
    'velocity_variance_X_smartwatch': velocityFeatsSW['varX']!,
    'velocity_mean_Y_smartwatch': velocityFeatsSW['meanY']!,
    'velocity_variance_Y_smartwatch': velocityFeatsSW['varY']!,
    'velocity_mean_Z_smartwatch': velocityFeatsSW['meanZ']!,
    'velocity_variance_Z_smartwatch': velocityFeatsSW['varZ']!,
    'angular_velocity_mean_X_smartwatch': angularVelocityFeats['meanX']!,
    'angular_velocity_variance_X_smartwatch': angularVelocityFeats['varX']!,
    'angular_velocity_mean_Y_smartwatch': angularVelocityFeats['meanY']!,
    'angular_velocity_variance_Y_smartwatch': angularVelocityFeats['varY']!,
    'angular_velocity_mean_Z_smartwatch': angularVelocityFeats['meanZ']!,
    'angular_velocity_variance_Z_smartwatch': angularVelocityFeats['varZ']!,
  };
}

/// Groups data by 'window_id' and computes features for each window.
List<Map<String, dynamic>> calculateFeatures(List<SensorRow> data) {
  // Group by window_id.
  Map<int, List<SensorRow>> groups = {};
  for (var row in data) {
    int windowId = row['window_id'] as int;
    groups.putIfAbsent(windowId, () => []).add(row);
  }
  List<Map<String, dynamic>> features = [];
  groups.forEach((windowId, rows) {
    Map<String, double> feats = calculateCombinedFeatures(rows);
    feats['window_id'] = windowId.toDouble();
    features.add(feats);
  });
  return features;
}

/// The full sensor data pipeline.
List<Map<String, dynamic>> sensorDataPipeline(List<SensorRow> rawData) {
  var preprocessed = loadAndPreprocessData(rawData);
  var cleaned = normalizeAndRemoveOutliers(preprocessed);
  var segmented = segmentData(cleaned);
  return calculateFeatures(segmented);
}

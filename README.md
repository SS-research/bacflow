# non-intrunsive BAC estimation

A research project on blood alcohol concentration (BAC) estimation from smart wearables.

## research statement

For a behind-the-scenes look at the research statement, see [this](https://chat.openai.com/share/795f4c63-6a0a-4271-b0cf-f02067d5798d) conversation with chat-GPT.

## research question

The primary objective of this research is to develop and validate a non-intrusive methodology for estimating blood alcohol concentration (BAC) using smart wearables. The key question guiding this research is whether the integration of machine learning models with biomarkers obtained from wearables can provide accurate and real-time assessments of alcohol influence in individuals, addressing the limitations of current intrusive measures.

## background

Driving under the influence (DUI) is a major contributor to road accidents, and existing BAC estimation methods, such as breathalyzers and Widmark-based models, suffer from limitations in availability, cost, and intrusiveness. To overcome these challenges, we propose leveraging smart wearables commonly worn by individuals, incorporating signals like blood temperature, pressure, oxygen levels, and gait information. This approach aims to offer a less obtrusive and continuous monitoring solution, potentially revolutionizing the field of alcohol influence detection.

## experimental setting

### collaboration with events and venues

- Identify and collaborate with social events or venues where participants voluntarily wear smart wearables.
- Implement a comprehensive informed consent process to explain the study's purpose and data collection methods.

### wearable distribution and calibration

- Provide participants with smart wearables equipped with relevant sensors.
- Conduct a calibration phase to establish baseline biomarker data during non-drinking periods.

### ground-truth measurement

- Integrate periodic BAC measurements using traditional breathalyzers strategically placed at the event.
- Choose a subset of actively participating individuals for accurate ground truth data.

### anonymized participant recognition

- Assign persistent anonymized identifiers to participants during their first engagement.
- Encourage voluntary registration with chosen identifiers, ensuring no direct link to personal information.

### incentives and food tracking

- Consider budget-friendly incentives for participants, such as discounted drinks or event merchandise.
- Implement non-intrusive food tracking mechanisms, such as QR codes, to gather data on stomach emptiness.

### data security and privacy

- Implement robust data security measures to protect participant identifiers and collected information.
- Clearly communicate the tracking and recognition processes to participants, ensuring transparency and compliance with privacy regulations.

### scientific significance

- Aim for a diverse participant pool to capture variations in drinking behavior and biomarker responses.
- Collaborate with universities or research institutions to enhance scientific rigor and data analysis expertise.

### longitudinal study design

- Plan for multiple events over an extended period to capture variations in alcohol influence under different circumstances.
- Develop a comprehensive data analysis plan to compare smart wearable data with traditional breathalyzer results.

This research seeks to bridge the gap between current intrusive methods and the need for a non-intrusive, continuous monitoring solution for alcohol influence, with the ultimate goal of enhancing road safety and public health.

## resources

- [get-BAC](https://getbacsoftware.org/)
- [Michaelis–Menten kinetics](https://en.wikipedia.org/wiki/Michaelis%E2%80%93Menten_kinetics)
- [drinkR - estimate your BAC](https://www.sumsar.net/blog/2014/07/estimate-your-bac-using-drinkr/)
- [drinkR - repository](https://github.com/rasmusab/drinkr)
- [BAC-simulator](https://github.com/bcyran/bac-simulator)
- [pybind11 - scikit-build](https://github.com/pybind/scikit_build_example)
- [pybind11 - setuptools](https://github.com/pybind/python_example)
- [pybind11 - chat-GPT](https://chat.openai.com/share/936bbecd-8445-48eb-ba65-0e49a2e95bd0)

---
layout: post
title: "A/B test analysis with bootstrapping"
tags:
- Bootstrapping
- Python
- A/B tests
---

In this post I'll give a hands-on walkthrough showing you how to analyse the impact of an A/B test using bootstrap sampling. I'll also compare this to the traditional approaches, to give you confidence that bootstrapping is working the way we expect.

# Intro

For a full introduction to bootstrapping, have a look at my post [here](here).

In this post we will:
1. Give a generic A/B test problem statement
1. Give a concrete example of this, with some data
1. Explain what kind of answer we're looking for
1. Give the traditional solution to the problem
1. Do it the bootstrapping way
1. Compare the two approaches

# A/B tests generic problem statement

The generic problem statement for A/B test analysis is something like this:
- We've run an A/B test, exposing some people to variant A, and some to variant B (also called the control and treatment).
- These users went on to do something (the objective).
- We'd like to know whether the intervention (the difference between the control and treatment) caused an increase in this objective (and perhaps we'd also like to know how big of an increase it caused).

# A concrete A/B testing problem statement

Let's create a simple scenario here.

In our Sushi delivery app, we offer users a discount code if they sign up for our newsletter. We currently show them a message with the text "Sign up to our newsletter for 5% off your next order".

Our marketing team has decided to try optimise this copy, to increase the number of people who sign up for the newsletter. They propose "Dive into exclusive deals by subscribing to our newsletter – our fin-tastic discount code will swim straight into your inbox, creating a wave of savings!" [Thanks ChatGPT].

So, here are the important parts here:
1. The control group will get the original copy ("Sign up...").
1. The treatment group will get the proposed copy ("Dive into...").
1. Our conversion metric is the rate at which users sign-up for the newsletter.

Right, let's create some synthetic data for this:

```python
import numpy as np
from np.random import random
from tqdm import tqdm

np.random.seed(2024)  # Set the seed for reproducibility

# Specify the metadata of the actual distribution 
# (we wouldn't know this in real life)
n_group = 1000

conversion_control = 0.1
conversion_treatment = 0.1 * 1.1  # There is a 10% uplift

# Create the synthetic sample data (this is what we'd get from
# running the experiment)
# Each of these is a binary outcome: did this user sign up
# when shown the message?
samples_control = random(n_group) <= conversion_control
samples_treatment = random(n_group) <= conversion_treatment
```

Right, so we have some (synthetic data). What kind of answer do we want from it?

Basically, we want to know whether the percentage of people in the treatment group who signed up is greater than the percentage of people in the control group, and if so, what the probability is of this occuring by chance (the p-value).

The first part of this is easy, we just calculate the uplift directly:
```python
print(f"Uplift: {samples_treatment.mean()/samples_control.mean()}")
```

Good. So there appears to be an uplift.

Now, how likely were we to see this uplift if it were caused by chance (i.e. both variants have the same likelihood of conversion, but more users in the treatment *just happened* to convert?)


```python


## The normal (boring) way - done after some Googling and comparing to this site:
# https://uk.surveymonkey.com/mp/ab-testing-significance-calculator/

# import statsmodels.stats.proportion
# statsmodels.stats.proportion.proportions_ztest(sum(samples_treatment)-sum(samples_control), n_group, alternative="larger")

from scipy.stats import ttest_ind

t, p = ttest_ind(samples_control, samples_treatment)
p_val_ttest = p / 2  # To account for 1 sided test
print(f"The ttest p_val: {p_val_ttest}")


## Now we just bootstrap it
num_iter = 1000
res = []
bootstrap_mean_control = []
bootstrap_mean_treatment = []
for _ in tqdm(range(num_iter)):
   bootstrap_sample_control = np.random.choice(samples_control, size=samples_control.size, replace=True)
   bootstrap_sample_treatment = np.random.choice(samples_treatment, size=samples_treatment.size, replace=True)
   bootstrap_mean_control.append(bootstrap_sample_control.mean())
   bootstrap_mean_treatment.append(bootstrap_sample_treatment.mean())

# Calculate p-value for treatment > control
p_val_bootstrap = np.less_equal(bootstrap_mean_treatment, bootstrap_mean_control).mean()

print(f"bootstrap p_val (with {num_iter} iterations): {p_val_bootstrap}")

fig = go.Figure()
fig.add_trace(go.Histogram(x=bootstrap_mean_control, name="control"))
fig.add_trace(go.Histogram(x=bootstrap_mean_treatment, name="treatment"))
fig.update_layout(barmode='overlay')
fig.update_traces(opacity=0.75)
fig.show()

## Get some confidence bounds
conf_bounds = np.quantile(np.divide(bootstrap_mean_treatment, bootstrap_mean_control), [0.05, 0.95])
print(f"90% confidence bounds: {conf_bounds}")

```




```python
{% include_relative  code_snippets/test_code.py %}
```


# The traditional approach

Okay, so if we didn't have bootstrapping as a tool, how would we go about solving this the traditional way?
For A/B tests, we always use some kind of hypothesis test. 

The statistical reasoning we follow is this:
- We propose a null hypothesis (the difference between the performance of the two variants is due to chance - i.e. our hypothesis is that there is no cause, hence *null*)
- We test how likely this null hypothesis is (this is the p-value). If it's sufficiently low, then we can reject this null hypothesis. Having rejected the null hypothesis, we assert that our hypothesis (that the difference in performance between the variants is due to the intervention).

So, we need a traditional approach to finding the probability of the data given the null hypothesis.

We reach into our toolbox of statistical tests for an appropriate test (or we reach for Google or ChatGPT).

In this case a 1-tailed test of proportions (TODO: check this)

(TODO: apply this)


# The bootstrapping approach

Instead, we can use bootstrapping to estimate this directly:

(TODO:

1. Explain that we're really just interested in whether we'd observe the same outcome if we repeated the test over and over. The best info we have of whether this would happen is our sample, so we bootstrap it to find out.
1. Each bootstrap sample is equivalent (i.e. our best guess) of what running the experiment again would yield
1. The p-value is then just the portion of these where the outcome holds (i.e. A > B) (TODO: I'm not sure I fully understand why - surely this is not really P(obs|H_null), but rather something like P(obd))


)

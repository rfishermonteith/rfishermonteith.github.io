---
layout: post
title: "A/B test analysis with bootstrapping"
tags:
- Bootstrapping
- Python
- A/B tests
---

In this post I'll give a hands-on walkthrough showing you how to analyse the **impact of an A/B test using bootstrap sampling**. I'll also compare this to the traditional approach, to give you confidence that bootstrapping is working the way we expect.

# Intro

For a full introduction to bootstrapping, have a look at my post [here]({% post_url 2024-02-02-intro-to-bootstrapping %}). [[TODO: update this link]]
[here]({% link _drafts/intro-to-bootstrapping.md %})

In this post we will:
1. Give a generic A/B test problem statement.
1. Give a concrete example of this, with some data.
1. Explain what kind of answer we're looking for.
1. Give the traditional solution to the problem.
1. Do it the bootstrapping way.
1. Compare the two approaches.

# A/B tests generic problem statement

The generic problem statement for A/B test analysis is something like this:
- We've run an A/B test, exposing some people to variant A, and some to variant B (also called the control and treatment).
- Some of these users went on to do something (the conversion goal).
- We'd like to know whether the intervention (the difference between the control and treatment) caused an increase in this goal (and perhaps we'd also like to know how big an increase it caused).

# A concrete A/B testing problem statement

Let's create a simple scenario here.

In our Sushi delivery app (Fishful Thinking), we offer users a discount code if they sign up for our newsletter. We currently show them a message with the text "Sign up to our newsletter for 5% off your next order".

Our marketing team has decided to try optimise this copy, to increase the number of people who sign up for the newsletter. They propose "Dive into exclusive deals by subscribing to our newsletter – our fin-tastic discount code will swim straight into your inbox, creating a wave of savings!" [Thanks ChatGPT].

So, here are the important parts:
1. The control group will get the original copy ("Sign up...").
1. The treatment group will get the proposed copy ("Dive into...").
1. Our conversion goal is the rate at which users sign-up for the newsletter.

Right, let's create some synthetic data for this:

```python
import numpy as np
from numpy.random import random
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

Right, so we have some (synthetic) data. What kind of answer do we want from it?

Basically, we want to know whether the percentage of people in the treatment group who signed up is greater than the percentage of people in the control group who did so, and if so, what the probability is of this occuring by chance (the p-value).

The first part of this is easy, we just calculate the uplift directly:
```python
print(f"Uplift: {samples_treatment.mean()/samples_control.mean()}")
```
```sh
Uplift: 54.29%
```

Good. So there appears to be an uplift (and a big one!).

Now, how likely were we to see this uplift if it were caused by chance (i.e. both variants have the same likelihood of conversion, but more users in the treatment *just happened* to convert?)

# The traditional approach

Okay, so if we didn't have bootstrapping as a tool, how would we go about solving this the traditional way?
For A/B tests, we always use some kind of hypothesis test. 

The statistical reasoning we follow is this:
- We propose a null hypothesis (that the difference between the performance of the two variants is due to chance - i.e. our hypothesis is that there is no cause, hence *null*)
- We test how likely this null hypothesis is (this is the p-value). If it's sufficiently low, then we can reject this null hypothesis. Having rejected the null hypothesis, we assert that our hypothesis is true (that the difference in performance between the variants is due to the intervention).

So, we need a traditional approach to finding the probability of the data given the null hypothesis.

We reach into our toolbox of statistical tests for an appropriate test (or we reach for Google or ChatGPT).

In this case a 1-tailed test of proportions (TODO: check this)

I usually check (or just do) this on a website like [https://uk.surveymonkey.com/mp/ab-testing-significance-calculator/](https://uk.surveymonkey.com/mp/ab-testing-significance-calculator/) (most plaforms which offer any kind of A/B testing give some calculators), since it's usually quicker than finding the right code to use.

```python
from scipy.stats import ttest_ind

_, p_val_ttest = ttest_ind(samples_control, samples_treatment, alternative="less")
print(f"The ttest p_val: {p_val_ttest:.2}")
```
```sh
The ttest p_val: 0.0014
```

So, that was reasonably easy (as long as we knew what test to use).

# The bootstrapping approach

Another approach is to use bootstrapping to estimate this directly.

To give some more intuition for what this is doing (you can also check out my full post [here]({% post_url 2024-02-02-intro-to-bootstrapping %}). [[TODO: update this link]]
[here]({% link _drafts/intro-to-bootstrapping.md %})):
- The p-value (from a frequentist perspective) is the frequency that we'd observe an effect size of this magnitude or larger, if these samples are drawn from the same distribution (i.e. that there is no effect).
- We can answer something slightly different (but equivalent). We can answer how likely it is that we would see a positive effect size if we repeated this experiment over and over again.
  - So, instead of calculating the p-value, we calculate the confidence interval, $\alpha$.
  - We can then convert this to the p-value using $p=1-\alpha$ (see [this post](https://statisticsbyjim.com/hypothesis-testing/hypothesis-tests-confidence-intervals-levels/) by Jim Frost - these are not the same thing, but they always agree - we'll see an example of this below).
- So, we generate bootstrap samples to simulate repeating the experiment:
  - Each bootstrap sample is our best guess of what running the experiment again would yield.
  - This distribution over possible outcomes gives our best guess for the range of uplift values we'd expect to see in the wild.
  - We can then draw confidence bounds from this distribution, and then extract the p-value from these.


Let's look at some code for how this works.


```python
## Now we just bootstrap it
num_iter = 10000
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

```

The key observation here is that we look at what percentage of the bootstrap samples led us to seeing the control beating the variant. This is equivalent to the p-value.

We can get a little more useful info out of the bootstrap though - we can get confidence bounds. These will be interpreted as the range of true uplift value 


```python

## Get some confidence bounds
conf_bounds = np.quantile(np.divide(bootstrap_mean_treatment, bootstrap_mean_control), [0.05, 0.95])
print(f"90% confidence bounds: {conf_bounds}")

```

```sh
90% confidence bounds: [1.21428571 1.98275862]
```

So, we're 90% confident that the true uplift value lies between 21% and 98%.

We can also plot this, which gives us (in my opinion) far more useful information about the performance of the A/B test.

TODO: add the chart showing the distribution of uplift values, and explain how to interpret this

TODO: add another chart showing the boxplot of the 90% CI, and how to interpret this

# Comparison between bootstrapping and the traditional way



# Some interesting things to note about bootstrapping for confidence bounds and p-values

1. The p-value you generate will only a precision of the inverse of the number of bootstrapping iterations you use. So, if you'd like to evaluate the significance at a level of 0.05, you'll need at least 20 simulations (and you should always aim for far, far more)
1. Confidence intervals are similarly affected, since they're just the quantiles of the bootstrapped measures, so having more bootstrap iterations will make these a little smoother (especially if you want more granular confidence bounds or distributions of the measure).

```python
{% include_relative  code_snippets/test_code.py %}
```


# Useful links:
1. [https://statisticsbyjim.com/hypothesis-testing/hypothesis-tests-confidence-intervals-levels/](https://statisticsbyjim.com/hypothesis-testing/hypothesis-tests-confidence-intervals-levels/) - explains that the p-value and confidence intervals always agree
1. [https://statisticsbyjim.com/hypothesis-testing/bootstrapping/](https://statisticsbyjim.com/hypothesis-testing/bootstrapping/) - describes bootstrapping and confidence bounds
1. 
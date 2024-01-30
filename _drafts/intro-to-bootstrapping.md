---
layout: post
title: "Intro to bootstrapping for confidence bounds"
---

I'll show you how to use bootstrapping, a powerful sampling technique which can be used to estimate confidence bounds, p-values and distributions for samples without the need to model (or understand) the underlying distributions.

# Who is this post for?

Have you ever needed to:
1. Find confidence bounds for a weird/complex calculation?
1. Needed to find p values for an A/B test with an unusual distribution or complex metric calculation?
1. Needed to find p values for an A/B test with simple distributions and been too lazy to check what hypothesis test to use?


If you answered yes to any of the above, then this post is for you!

# Intro

In this post, I hope to:
1. Get you wildly excited about the strengths of bootstrapping.
1. Explain some of the use cases for it.
1. Give a clear, intuitive description of what it is and how it works.
1. Give some example code to show how to carry out bootstrapping.
1. Discuss some of the risks and pitfalls.
1. Refer to some good resources where you can learn more.

## A quick aside about why I fell in love with bootstrapping
(if you just want get straight to the technical details, feel free to [jump ahead](#what-is-bootstrapping))

Some years ago (reasonably early in my career - probably in 2018 or so), when I was working on some kind of forecasting project, where we were attempting to forecast something like sales volumes or stock levels or occupancy levels or something, we came across an interesting quandry. We had very limited historic training data, and so had relatively little confidence in the forecasts. We used a collection of different predictive models (including ARIMA-style models, some linear and logistic regression ones, and eventually a NN), and blended the predictions.

The issue was that we needed to explain to our client just how confident we were (or weren't) in the forecasts.

While each model (or most at least) that we built had the ability to produce confidence bounds, these seemed far too tight, given how much volatility we could see in the historic data.

We[^1] hit on a good idea (although one with questionable justification, which I'll address below). That idea was to train a set of simple neural networks (NNs) on subsets of the data, and then use the distribution of the predictions of these NNs to create some nice shaded regions around the forecasts we were giving. We knew that NNs behaved weirdly in regression settings when extrapolating, and that this was 'stochastic' (in this sense just very sensitive to the initial node weights and the training data).

This did exactly what we wanted - we had nice graphs to show the client which gave a visual demonstration of our reasonably low confidence.

However, it was also wrong, for a few reasons:
1. We had no principled way to choose how to subset the data when training the iterations of the NN. We knew that using small subsamples gave wider prediction bounds, but didn't know what the right size was.
1. While the shaded areas we could put on the plots were *useful*, they had no objective meaning.

And that's where the story ended, for a few years.

And then, in 2021 or 2022, I came across bootstrapping, and my life changed for good.

# What is bootstrapping

We can phrase this in a few ways, at least one of which will make sense to you, depending on your background and experience (hopefully!):

1. Bootstrapping is a non-parametric way to estimate a population measure from a sample.
1. Bootstrapping is an algorithm which gives equally likely outcomes for some sampled outcome, as if you resampled.

In short, bootstrapping is an approach (or algorithm) for estimating some measure of some population, based solely on the sample we have available.

## Some examples where bootstrapping may be helpful

1. You've run an A|B test. What are the range of uplift values might you expect?<br>
This is another way of saying: "if we ran this experiment over and over again, what range of uplift values would we expect to see?"
1. We fit a model to some data, where the coefficients in the model have some physical interpretation. What range of coefficient values should we expect to see if we retrained the model on new data?
1. We calculate some business metric (e.g. average cost per order) and would like to know how much this might vary for the next month.

Hopefully you can see where this is going. Anytime we calculate a thing based on a sample of data from some population, and we're interested to know what the distribution of this thing is, then bootstrapping can help.

## How would this traditionally be solved?

For each of the examples mentioned above, there are standard, robust approaches to estimating these things without resorting to bootstrapping.

Specifically for the above:
1. We can pick an appropriate hyopthesis test, based on what we know about the distribution. This will allow us to calculate a p-value, and some confidence bounds. In some cases, this can be quite challenging (if either it's a complex distribution, an unknown distribution, or you don't know lots of stats)
1. Depending on the model you're fitting, it may have a way to calculate confidence bounds on its coefficients directly (e.g. the Python `statsmodel` linear regression models have a [`conf_int` method](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.conf_int.html), which will directly return confidence bounds. This is based on the Student's t-distribution. See [^2]). Sometimes though, there will either be no way to calculate these confidence bounds, or you may not know how to do it, or even implement it.
1. If we know how this measure is distributed, we can estimate this by using some stats directly (but this only works if the distribution is "well behaved").

So, while there are sometimes approaches to solving these problems using some stats knowledge, sometimes we either can't, or don't know enough to know how.

In these cases, bootstrapping to the rescue!

## So, what exactly is bootstrapping?

Bootstrapping relies on being able to use the sample you have to generate equally likely samples (hence the term 'bootstrapping', as in pulling yourself by your own bootstraps).

So, we generate lots (usually 1000s) of bootstrap samples from our data. We pretend that each of these is actually a new sample. We calculate the thing on it, and this forms a distribution we can use for whatever we want (getting p-values, confidence bounds, plotting etc)

The magic piece of this is how you generate the bootrap samples, and this is by **sampling with replacement**.

So, the process is as follows:
1. Take your sample data, generate $n$ samples with replacement (of the same size of the original data).\*
1. For each of these samples, calculate the thing you care about.
1. Use this however you want.

> \* Why does this work?
> 
> For a full explanation see [this section](#why-does-it-work). In short, this sample data is the best representation we have of the population, so by redrawing samples with replacement, we're doing our best to simulate what would happen if we had to redraw the sample from the population. Sometimes, we'll draw some of the elements more than once, and sometimes not at all. In this way outliers are sometimes drawn, sometimes not, and sometimes drawn multiple times - this serves to stretch out this distribution in a way that's consistent with our best guess for the data we'd get if we redrew from the population.


## An example in code

Below is some sample code for how to apply the bootstrap process to estimate the distribution and 90% confidence bounds for the mean value of a uniform distribution.

It's worth noting that the complexity of the `run_bootstrap` function is seldom more complex than this for most applications (in my experience at least).

```python
import numpy as np
from tqdm import tqdm  # Just to get nice progress meters


# A function which computes a measure (in this case a mean value)
def calculate_measure(data):
    return data.mean()


def run_bootstrap(sample_data, num_iter=1000):
    bootstrap_measures = np.empty(shape=0)
    for _ in tqdm(range(num_iter)):
        bootstrap_sample = np.random.choice(sample_data, size=sample_data.size, replace=True)
        bootstrap_measure = calculate_measure(bootstrap_sample)
        bootstrap_measures = np.append(bootstrap_measures, bootstrap_measure)
    
    return bootstrap_measures


# We have some data that was sampled from somewhere (we'll make some up)
np.random.seed(1)


samples = np.random.random(478)  # We have a set of 478 samples from the population, drawn from the uniform distribution

bootstrap_measures = run_bootstrap(samples)

# We now have a distribution of the sample mean, we can do whatever we want
print(f"Expected value: {bootstrap_measures.mean()}")
print(f"90% confidence bounds: {np.quantile(bootstrap_measures, [0.05, 0.95])}")

```

When you run this, you'll get the following:

```bash
100%|██████████| 1000/1000 [00:00<00:00, 36131.32it/s]
Expected value: 0.5075680220514992
90% confidence bounds: [0.48611194 0.52922992]
```
Nothing too surprising here: 
1. The expected value of this distribution from the bootstrap estimation is 0.508, where the true value is 0.5 (knowing what we know about the distribution the sample was drawn from)
1. The 90% confidence bounds are wrapped tightly around 0.5. The interpretation for this is: "if we had to draw new samples from the population, and recalculate the mean, 90% of the time these would be between these two values"



# The rest of the story
1. Give some more examples on using it
    1. A\|B test (With p-values) 
    1. 

[^1] If my colleague ever reads this, and *doesn't* think it was a good idea, then just know I'm happy to take full responsibility for it.

[^2] See [this post](https://medium.com/@jcatankard_76170/linear-regression-parameter-confidence-intervals-228f0be5ea82) by Josh Tankard for some sleuthing on the matter

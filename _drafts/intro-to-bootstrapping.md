---
layout: post
title: "Intro to bootstrapping"
---

# Who is this for?

Have you ever needed to:
1. Find confidence bounds for a weird/complex calculation?
1. Needed to find p values for an A/B test with an unusual distribution or complex metric calculation?
1. Needed to find p values for an A/B test with simple distributions and been too lazy to check what test to use?


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

(if you just want get straight to the technical details, feel free to jump ahead)

Some years ago (reasonably early in my career - probably in 2018 or so), I was working on some kind of forecasting project, where we were attempting to forecast something like sales volumes or stock levels or occupancy levels or something, we came across an interesting quandry. We had very limited historic training data, and so had relatively little confidence in the forecasts. We used a collection of different predictive models (including ARIMA-style models, some linear and logistic regression ones, and eventually a NN), and blended the predictions.

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


# Some maths
$$ x = /sum{y} $$

[^1] If my colleague ever reads this, and *doesn't* think it was a good idea, then just know I'm happy to take full responsibility for it.
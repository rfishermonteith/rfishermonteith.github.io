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
- We've run an A/B test, exposing some people to variant A, and some to variant B (also called the control and variant).
- These users went on to do something (the objective).
- We'd like to know whether the intervention (the difference between the control and variant) caused an increase in this objective (and perhaps we'd also like to know how big of an increase it caused).

# A concrete A/B testing problem statement

Let's create a simple scenario here.

In our Sushi delivery app, we offer users a discount code if they sign up for our newsletter. We currently show them a message with the text "Sign up to our newsletter for 5% off your next order".

Our marketing team has decided to try optimise this copy, to increase the number of people who sign up for the newsletter. They propose "Dive into exclusive deals by subscribing to our newsletter – our fin-tastic discount code will swim straight into your inbox, creating a wave of savings!" [Thanks ChatGPT].

So, here are the important parts here:
1. The control group will get the original copy ("Sign up...").
1. The variant group will get the proposed copy ("Dive into...").
1. Our conversion metric is the rate at which users sign-up for the newsletter.

Right, let's create some synthetic data for this:

```python

A = 1

```









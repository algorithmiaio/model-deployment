# Developing an XGBoost model on a Jupyter notebook and deploying to Algorithmia

This Jupyter notebook to Algorithmia example is to demonstrate how you can programmatically create an algorithm on [Algorithmia](https://algorithmia.com), train a model and deploy it for serving, all from within your Jupyter notebook.

Step by step, we will:

- Create an algorithm on Algorithmia
- Clone the algorithm's repository on our local machine, so that we develop it locally
- Create the basic algorithm script and the dependencies file. We will code our script in advance, assuming that our model will be sitting on a remote path on - Algorithmia and our script will load the model from there. We will then make these assumptions true!
- Commit and push these files to Algorithmia and get our Algorithm's container built
- Load our training data
- Preprocess the data
- Setup an XGBoost model and do a mini hyperparameter search
- Fit the data on our model
- Get the predictions
- Check the accuracy
- Repeat the model development iterations until we are happy with our model :)

And finally, once we are happy with the model performance, we will upload it to Algorithmia and have it up and ready to serve our upcoming prediction requests!


You can also check out the built algorithm at https://algorithmia.com/algorithms/asli/xgboost_basic_sentiment_analysis and see the final product in action.

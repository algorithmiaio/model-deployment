# Model Monitoring & Auto Deployment on Algorithmia

This tool will automatically promote new versions of a deployed algorithm by the criteria defined in the source-code.

To get it working, make sure to do the following:

1. Create a new MYSQL DB, and add the credentials to the source code. (We used AWS RDS Aurora for testing & development)
2. Create a new target algorithm that will be monitored. And update the `algo_name` variable.
4. Change the `resolve_experiment()` function if you want to use a different criteria for deploying new models.

After doing the following above, everything should work automatically. Instead of calling the target algorithm directly, you can now call this orchestration algorithm instead.

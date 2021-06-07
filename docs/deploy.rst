=============
Deploying MDN
=============

MDN is served from `Amazon Web Services`_ in the US West (Oregon)
datacenters. MDN is deployed as Docker_ containers managed by Kubernetes_. The
infrastructure is defined within MDN's `infra repository`_, including the tools
used to `deploy and maintain MDN`_.

.. _`Amazon Web Services`: https://en.wikipedia.org/wiki/Amazon_Web_Services
.. _Docker: https://www.docker.com/
.. _Kubernetes: https://kubernetes.io/
.. _`infra repository`: https://github.com/mdn/infra
.. _`deploy and maintain MDN`: https://github.com/mdn/infra/tree/master/apps/mdn/mdn-aws

Deploying new code to AWS takes several steps, and about 60 minutes for the
full process. The deployer is responsible for emergency issues for the next 24
hours. There are 1-3 deployments per week, usually between 7 AM and 1 PM
Pacific, Monday through Thursday.

.. Note::

   This page describes deployment performed by MDN staff. It requires
   additional setup and permissions not described here. Deployments will
   not work for non-staff developers, and should not be attempted.

.. _Pre-Deployment:

Pre-Deployment
--------------

Before deploying, a staff member should:

* Check the latest images from master are built by Jenkins_
  (`Kuma master build`_, both private to staff),
  and uploaded to the DockerHub_ repositories
  (`Kuma images`_).

.. _Dennis: https://github.com/willkg/dennis
.. _Jenkins: https://ci.us-west-2.mdn.mozit.cloud
.. _Kuma: https://github.com/mdn/kuma/actions
.. _Pontoon: https://pontoon.mozilla.org/projects/mdn/
.. _`Kuma images`: https://hub.docker.com/r/mdnwebdocs/kuma/tags/
.. _`Kuma master build`: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/activity/?branch=master
.. _`master build`: https://travis-ci.com/mdn/kuma
.. _`mdn-browser-compat-data`: https://www.npmjs.com/package/mdn-browser-compat-data
.. _`open a pull request`: https://github.com/mdn/kuma
.. _mdn-l10n: https://github.com/mozilla-l10n/mdn-l10n
.. _DockerHub: https://hub.docker.com/


Deploy to Staging
-----------------
The staging site is located at https://developer.allizom.org.  It runs on the
same Kuma code as production, but against a different database, other backing
services, and with less resources. It is used for verifying code changes before
pushing to production.

* Start the staging push, by updating and pushing the ``stage-push`` branches::

    git fetch origin
    git checkout stage-push
    git merge --ff-only origin/master
    git push

* Prepare for testing on staging:

  * Look at the changes to be pushed (`What's Deployed on Kuma`_). To enlist the help of pull request
    authors and others, you can report bug numbers and PRs in Matrix.
  * Think about manual tests to confirm the code changes work without errors.

* Merge and push to the ``stage-integration-tests`` branch::

    git checkout stage-integration-tests
    git merge --ff-only origin/master
    git push

  This will kick off `functional tests`_ in Jenkins_, which will also report
  to ``#mdndev``.

* Manually test changes on https://developer.allizom.org. Look for server errors
  on homepage and article pages. Try to verify features in the newly pushed
  code. Check the `functional tests`_.

* Announce in Slack (#mdn-dev) that staging looks good, and you are pushing to production.

.. _Jenkins: https://ci.us-west-2.mdn.mozit.cloud
.. _`What's Deployed on Kuma`: https://whatsdeployed.io/s-HC0
.. _`functional tests`: https://ci.us-west-2.mdn.mozit.cloud/blue/organizations/jenkins/kuma/branches

Deploy to Production
--------------------
The production site is located at https://developer.mozilla.org. It is
monitored by the development team and MozMEAO.

* Pick a push song on https://www.youtube.com. Post link to Matrix.

* Start the production push::

    git fetch origin
    git checkout prod-push
    git merge --ff-only origin/master
    git push

* For the next 30-60 minutes,

  * Watch https://developer.mozilla.org
  * Monitor MDN in New Relic for about an hour after the push, for increased
    errors or performance changes.
  * Start the :ref:`standby environment deployment <Deploy to Standby Environment>`
  * Close bugs that are now fixed by the deployment
  * Move relevant Taiga cards to Done
  * Move relevant Paper cut cards to Done

.. _Deploy to Standby Environment:

Deploy to Standby Environment
-----------------------------
The standby environment is located in the AWS EU Frankfurt datacenter. It runs
the same code and database as production, but runs in read-only
:ref:`maintenance mode <maintenance-mode>` and on minimal resources. It will
be scaled up and handle MDN traffic if there is a critical failure in
the AWS US West datacenter.

* Start the standby environment push::

    git fetch origin
    git checkout standby-push
    git merge --ff-only origin/master
    git push

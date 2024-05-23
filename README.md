# PySigmaKoki
Python module to control Sigma Koki stages

# Install
    $ pip install pysigmakoki

# Example
    >>> import sigma_koki
    >>> gsc02 = sigma_koki.GSC02()
    >>> gsc02.open('/dev/tty.usbserial-FTT75V89A')
    >>> gsc02.setSpeed(1, 50, 20000, 1000, 50, 20000, 1000)
    >>> gsc02.returnToMechanicalOrigin('+', '+')
    >>> gsc02.move(-50000, -50000)
    >>> gsc02.getStatus()
    '-    50000,-    50000,K,K,R'

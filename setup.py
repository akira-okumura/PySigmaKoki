from distutils.core import setup
import sigma_koki

setup(name='PySigmaKoki',
      version='1.0.0',
      description='Python Interface for Instruments by Sigma Koki',
      author='Akira Okumura',
      author_email='oxon@mac.com',
      license='BSD License',
      platforms=['MacOS :: MacOS X', 'POSIX', 'Windows'],
      url='https://sourceforge.net/p/pysigmakoki/',
      py_modules=['sigma_koki'],
      install_requires=['pyserial'],
      classifiers=['Topic :: Terminals :: Serial',
                   'Development Status :: 4 - Beta',
                   'Programming Language :: Python',
                   ],
      long_description=sigma_koki.__doc__
      )

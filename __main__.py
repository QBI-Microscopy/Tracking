import sys
from PyQt5 import QtCore, QtWidgets
from trackerapp import MyApp

def main(args=None):
    if args is None:
        args = sys.argv[1:]
        
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = MyApp()
    MainWindow.show()
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
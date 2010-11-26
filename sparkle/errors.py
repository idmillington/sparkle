class SparkleErrorBase(Exception):
    def __init__(self, message, position):
        super(SparkleErrorBase, self).__init__(message)
        self.position = position

class SparkleInternalError(SparkleErrorBase):
    pass

class SparkleSyntaxError(SparkleErrorBase):
    pass

class SparkleError(SparkleErrorBase):
    pass

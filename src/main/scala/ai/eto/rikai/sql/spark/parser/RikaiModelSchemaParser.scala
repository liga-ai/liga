package ai.eto.rikai.sql.spark.parser

import scala.collection.JavaConverters._
import org.apache.spark.sql.types._
import ai.eto.rikai.sql.spark.parser.RikaiModelSchemaParser._
import org.antlr.v4.runtime.{CharStreams, CommonTokenStream}
import org.apache.spark.sql.rikai.RikaiUDTRegistration

class SparkDataTypeVisitor extends RikaiModelSchemaBaseVisitor[DataType] {
  override def visitUnquotedIdentifier(
      ctx: UnquotedIdentifierContext
  ): DataType = {
    val name = ctx.getText
    val _SPARK_TYPE_MAPPING = Map(
      "bool" -> BooleanType,
      "boolean" -> BooleanType,
      "byte" -> ByteType,
      "tinyint" -> ByteType,
      "short" -> ShortType,
      "smallint" -> ShortType,
      "int" -> IntegerType,
      "long" -> LongType,
      "bigint" -> LongType,
      "float" -> FloatType,
      "double" -> DoubleType,
      "str" -> StringType,
      "string" -> StringType,
      "binary" -> BinaryType
    )
    if (_SPARK_TYPE_MAPPING.contains(name)) {
      _SPARK_TYPE_MAPPING(name)
    } else if (RikaiUDTRegistration.exists(name)) {
      RikaiUDTRegistration.getUDT(name).get
    } else {
      throw new RuntimeException(s"No such data type ${name}")
    }
  }

  override def visitStructType(
      ctx: StructTypeContext
  ): StructType = {
    val fields = ctx
      .field()
      .asScala
      .map { field =>
        val context =
          field.asInstanceOf[StructFieldContext]
        val name = context.name.getText
        val dataType = this.visitStructField(context)
        StructField(name, dataType)
      }
    StructType(fields)
  }

  override def visitStructField(ctx: StructFieldContext): DataType = {
    this.visitChildren(ctx.fieldType())
  }

  override def visitArrayType(ctx: ArrayTypeContext): DataType = {
    ArrayType(this.visitChildren(ctx.fieldType()))
  }
}

object ModelSchemaParser {
  def parse_schema(schema: String): DataType = {
    val lexer = new RikaiModelSchemaLexer(
      new UpperCaseCharStream(CharStreams.fromString(schema))
    )
    val tokens = new CommonTokenStream(lexer)
    val parser = new RikaiModelSchemaParser(tokens)
    val visitor = new SparkDataTypeVisitor
    visitor.visitSchema(parser.schema())
  }
}
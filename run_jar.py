import subprocess, json

s = """
public class Test {
    private NumberFormat parseFormatter(Context context, Arguments args){
        final String format = args.get(FORMAT_PARAM_NAME);
        final Locale locale = context.get(LOCALE);
        if (format != null){
            return new DecimalFormat(format, DecimalFormatSymbols.getInstance(locale));
        }
        int i = 10;
    }
}
"""
tree = subprocess.check_output(['java', '-jar', 'mavenproject1-1.0-SNAPSHOT-jar-with-dependencies.jar', s])

tree_json = json.loads(tree)

print(tree_json)
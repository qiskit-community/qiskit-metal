@import AppKit;

int main() {
	@autoreleasepool {
		NSWorkspace *workspace = [NSWorkspace sharedWorkspace];
		NSArray *args = [NSProcessInfo processInfo].arguments;

		if (args.count == 1) {
			return 1;
		}

		NSString *ret;
		NSString *app = args[1];

		if ([app rangeOfString:@"."].location != NSNotFound) {
			ret = [workspace absolutePathForAppBundleWithIdentifier:app];
		} else {
			ret = [workspace fullPathForApplication:app];
		}

		if (!ret) {
			return 2;
		}

		puts(ret.UTF8String);
	}

	return 0;
}